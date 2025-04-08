import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Any, Literal
from app.services.assesments.context_retriever import  SkillContextRetriever
from app.services.assesments.context_retriever import TestConfig, TestPlanner
import json
from motor.motor_asyncio import AsyncIOMotorClient
from app.repository.assessment_repository import MongoDBHandler
import re
from dataclasses import dataclass, field
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
from pymongo import MongoClient
from pydantic import BaseModel, Field

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MONGO_URI = "mongodb+srv://doadmin:67K98DEUBAY0T214@lwai-mongo-c557243a.mongo.ondigitalocean.com/stale?authSource=admin&tls=true"
DB_NAME = 'chatur'
MODEL_NAME = "gpt-4o"  
MAX_RETRIES = 3
BATCH_SIZE = 30
MAX_WORKERS = 5

@dataclass
class QuestionBatch:
    """Represents a batch of questions to be generated."""
    
    skill: str
    questions: List[Dict] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    target_count: int = BATCH_SIZE
    difficulty_distribution: Dict[str, float] = field(default_factory=dict)


class ContextBasedQuestionGenerator:
    """Generates multiple-choice questions based on skill context using structured output."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the question generator.
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.difficulty_criteria = {
            "easy": {
                "description": "Basic concept understanding and simple operations",
                "cognitive_level": "Remember and Understand",
                "complexity": "Single concept, straightforward application"
            },
            "moderate": {
                "description": "Multi-step problems, concept application, and analysis",
                "cognitive_level": "Apply and Analyze",
                "complexity": "Multiple concepts, requires understanding relationships"
            },
            "hard": {
                "description": "Complex problem-solving, edge cases, and advanced concepts",
                "cognitive_level": "Evaluate and Create",
                "complexity": "Multiple concepts with non-obvious interactions, requires deep understanding"
            }
        }
        self.difficulty_guidelines = {
            "easy": """
                - Tests basic understanding of simple concepts
                - Single operation or straightforward syntax
                - Direct application of fundamental knowledge
                Example easy question for Python:
                "What is the correct way to check if a key exists in a dictionary?"
                """,
            "moderate": """
                - Requires understanding of multiple concepts
                - Involves problem-solving with multiple steps
                - Tests edge cases and common pitfalls
                Example moderate question for Python:
                "Given a list comprehension that filters prime numbers and applies a lambda function, what would be the output?"
                """,
            "hard": """
                - Tests advanced concepts and their interactions
                - Requires deep understanding of language internals
                - Involves complex scenarios and optimization
                Example hard question for Python:
                "How would changing the implementation of a custom iterator affect memory usage in a generator pipeline processing large datasets?"
                """
        }

    def _create_question_prompt(self, context: Dict, skill: str, 
                               num_questions: int, difficulty_dist: Dict[str, float]) -> str:
        """
        Create a prompt for generating questions.
        
        Args:
            context: Context information for the skill
            skill: Skill name
            num_questions: Number of questions to generate
            difficulty_dist: Distribution of difficulty levels
            
        Returns:
            Formatted prompt string
        """
       
        difficulty_counts = {
            level: int(num_questions * ratio)
            for level, ratio in difficulty_dist.items()
        }
      
        total = sum(difficulty_counts.values())
        if total < num_questions:
            difficulty_counts['moderate'] += num_questions - total

        content = context.get('content', '')
        titles = context.get('titles', [])
        title = titles[0] if titles else ''
            
        prompt = f"""
       
        You are an expert assessment creator for {skill}. Generate EXACTLY {num_questions} high-quality multiple-choice questions following these specific difficulty guidelines.
        Question Distribution:
        {json.dumps(difficulty_counts, indent=2)}    
        IMPORTANT: YOU MUST GENERATE EXACTLY {num_questions} QUESTIONS. NOT {num_questions-1}, NOT {num_questions+1}, BUT EXACTLY {num_questions}.


        Context Title: {title}
        Context Content: {content[:10000]}  # Truncate context to prevent token limits

        STRICT DIFFICULTY GUIDELINES:
        Easy Questions:
        {self.difficulty_guidelines['easy']}

        Moderate Questions:
        {self.difficulty_guidelines['moderate']}

        Hard Questions:
        {self.difficulty_guidelines['hard']}

        CRITICAL REQUIREMENTS:
        1. Questions MUST match their designated difficulty level - no easy questions labeled as moderate/hard
        2. For programming skills:
           - Easy: Basic syntax, single operations, fundamental concepts
           - Moderate: Multi-step operations, data structure manipulation, algorithm understanding, algorithm implementation.
           - Hard: Performance implications, advanced patterns, edge cases, internals
        3. Each difficulty level should test progressively more complex cognitive skills:
           - Easy: Remember and understand
           - Moderate: Apply and analyze
           - Hard: Evaluate and create
        4. Include tricky distractors that test common misconceptions
        5. For programming questions, include code snippets that test real-world scenarios
        6. Generate questions that require problem-solving rather than just recall
        7. Include detailed explanations that cover why wrong answers are incorrect
        8. For each skill tested, ALWAYS include the main skill "{skill}" plus additional related skills

        Return EXACTLY {num_questions} questions that match the requested format, reflecting the specified difficulty distribution.
        """
        return prompt

    def normalize_question_format(self, question: Dict) -> Dict:
        """
        Normalize question format to match the required structure.
        
        Args:
            question: Original question dictionary
            
        Returns:
            Normalized question dictionary
        """
        key_mapping = {
            'question': 'questionText',
            'difficulty': 'difficultyLevel'
        }
        
        normalized = {}
        for old_key, new_key in key_mapping.items():
            if old_key in question:
                normalized[new_key] = question[old_key]
                
        # Copy over keys that don't need transformation
        for key in question:
            if key not in key_mapping:
                normalized[key] = question[key]
                
        # Convert answer to list if it's a string
        if 'answer' in normalized and not isinstance(normalized['answer'], list):
            normalized['answer'] = [normalized['answer']]
            
        return normalized
    def is_valid_question(self, question: Dict) -> bool:
        """
        Check if a question meets all validation criteria.
        
        Args:
            question: Question to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check for required keys
        required_keys = ['questionText', 'options', 'answer', 'difficultyLevel']
        if not all(k in question for k in required_keys):
            logger.warning(f"Question missing required keys: {question.get('questionText', 'Unknown question')}")
            return False
            
        # Check options - MUST HAVE EXACTLY 4 OPTIONS
        if len(question['options']) != 4:
            logger.warning(f"Question has {len(question['options'])} options instead of 4: {question.get('questionText', 'Unknown question')}")
            return False
        
        # Check answer exists
        if not question['answer']:
            logger.warning(f"Question has no answer: {question.get('questionText', 'Unknown question')}")
            return False
        
        # If everything passes, the question is valid
        return True
    
    def _validate_questions(self, questions: List[Dict], batch: QuestionBatch) -> List[Dict]:
        """
        Validate questions and attempt to fix common issues before validation.
        
        Args:
            questions: List of questions to validate
            batch: Batch configuration
            
        Returns:
            List of valid questions
        """
        valid_questions = []
        fixed_questions = 0
        
        for question in questions:
            fixed_question = self._fix_question_format(question)
            
            # If we successfully fixed the question, count it
            if fixed_question != question:
                fixed_questions += 1
                
            # Check if the fixed question is valid
            if self.is_valid_question(fixed_question):
                valid_questions.append(fixed_question)
                continue
                
            # If still not valid, try normalizing and revalidating
            normalized_question = self.normalize_question_format(fixed_question)
            if self.is_valid_question(normalized_question):
                valid_questions.append(normalized_question)
                continue
                
            # Log invalid questions that couldn't be fixed
            logger.warning(f"Question validation failed even after fixing attempts: {question.get('questionText', 'Unknown question')}")
                
            if len(valid_questions) >= batch.target_count:
                break
                
        logger.info(f"Fixed {fixed_questions} questions during validation")
        return valid_questions
    
    def _fix_question_format(self, question: Dict) -> Dict:
        """
        Attempt to fix common issues with question format.
        
        Args:
            question: Original question dictionary
            
        Returns:
            Fixed question dictionary
        """
        # Create a copy to avoid modifying the original
        fixed = question.copy()
        
        # 1. FIX OPTIONS COUNT (Most common issue)
        if 'options' in fixed and len(fixed['options']) != 4:
            # Check if we need to add a "None of the above" option
            if len(fixed['options']) == 3:
                fixed['options'].append("None of the above")
                logger.info(f"Added 'None of the above' option to question: {fixed.get('questionText', 'Unknown question')}")
                
            # Handle cases with too many options
            if len(fixed['options']) > 4:
                # Keep the correct option(s) and the first few distractors
                answers = fixed.get('answer', [])
                if not isinstance(answers, list):
                    answers = [answers]
                    
                # Find which options are answers
                answer_indices = []
                for answer in answers:
                    for i, option in enumerate(fixed['options']):
                        if answer == option:
                            answer_indices.append(i)
                            break
                
                # Create a new options list with answers and enough distractors to make 4
                new_options = []
                for i, option in enumerate(fixed['options']):
                    if i in answer_indices or len(new_options) < 4 - len(answer_indices):
                        new_options.append(option)
                        
                fixed['options'] = new_options[:4]
                logger.info(f"Trimmed options to 4 for question: {fixed.get('questionText', 'Unknown question')}")
        
        # 2. FIX ANSWER FORMAT
        if 'answer' in fixed and not isinstance(fixed['answer'], list):
            fixed['answer'] = [fixed['answer']]
            
        # 3. ENSURE ANSWER IS IN OPTIONS
        if 'answer' in fixed and 'options' in fixed and isinstance(fixed['answer'], list):
            answer_in_options = False
            for answer in fixed['answer']:
                if answer in fixed['options']:
                    answer_in_options = True
                    break
                    
            if not answer_in_options and fixed['answer']:
                # Try to find a close match in the options
                answer_text = fixed['answer'][0]
                closest_match = None
                for option in fixed['options']:
                    if answer_text.lower() in option.lower() or option.lower() in answer_text.lower():
                        closest_match = option
                        break
                        
                if closest_match:
                    fixed['answer'] = [closest_match]
                    logger.info(f"Fixed answer to match available option for question: {fixed.get('questionText', 'Unknown question')}")
                else:
                    # If no match found, set answer to the first option as a fallback
                    fixed['answer'] = [fixed['options'][0]]
                    logger.warning(f"Answer not in options, defaulted to first option for question: {fixed.get('questionText', 'Unknown question')}")
        
        return fixed    

    
    async def _generate_batch_questions(self, batch: QuestionBatch, retry_count: int = 0) -> List[Dict]:
        """
        Generate questions for a single batch using structured output format.
        
        Args:
            batch: Question batch configuration
            retry_count: Current retry attempt
            
        Returns:
            List of generated questions
        """
        try:
            prompt = self._create_question_prompt(
                batch.context,
                batch.skill,
                batch.target_count,
                batch.difficulty_distribution
            )
    
            # Define a modified Pydantic model without defaults
            class QuizQuestionNoDefault(BaseModel):
                questionText: str
                options: List[str]
                answer: List[str]
                difficultyLevel: Literal["easy", "moderate", "hard"]
                category: str
                explanation: str
                skillsTested: List[str]
                cognitive_level: str
    
            class QuizResponse(BaseModel):
                quest: List[QuizQuestionNoDefault]
    
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.beta.chat.completions.parse(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are an expert assessment creator. Generate multiple-choice questions with the exact format requested."},
                        {"role": "user", "content": prompt[:5000]} 
                    ],
                    max_completion_tokens=6000,
                    response_format=QuizResponse
                )
            )
            
            questions_data = response.choices[0].message.parsed
            questions = questions_data.quest 
            questions_dicts = [q.dict() for q in questions]
            
            for question in questions_dicts:
                question['user_response'] = ""
            
            valid_questions = self._validate_questions(questions_dicts, batch)
            
            logger.info(f"Generated {len(valid_questions)} valid questions out of {len(questions_dicts)} for {batch.skill}")
            return valid_questions
                
        except Exception as e:
            if retry_count < MAX_RETRIES:
                logger.error(f"Error generating structured questions for {batch.skill}: {str(e)}. Retry {retry_count + 1}/{MAX_RETRIES}")
                return await self._generate_batch_questions(batch, retry_count + 1)
            else:
                logger.error(f"Failed to generate structured questions for {batch.skill} after {MAX_RETRIES} retries: {str(e)}")
                return []
          
    async def _generate_questions_for_skill(self, skill: str, context: Dict, total_needed: int, 
                                          difficulty_distribution: Dict[str, float]) -> List[Dict]:
        """
        Generate questions for a specific skill by breaking into batches.
        """
        all_questions = []
        remaining_to_generate = total_needed
    
        if total_needed <= BATCH_SIZE:
            logger.info(f"Generating {total_needed} questions for {skill} in a single batch")
            batch = QuestionBatch(
                skill=skill,
                context=context,
                target_count=total_needed,
                difficulty_distribution=difficulty_distribution
            )
            
            for attempt in range(MAX_RETRIES):
                if remaining_to_generate <= 0:
                    break
                    
                batch.target_count = remaining_to_generate
                questions = await self._generate_batch_questions(batch)
                
                questions_to_add = questions[:remaining_to_generate]
                all_questions.extend(questions_to_add)
                remaining_to_generate -= len(questions_to_add)
                
                if remaining_to_generate <= 0:
                    break
                    
                logger.info(f"Got {len(questions_to_add)} valid questions, need {remaining_to_generate} more")
    
            return all_questions[:total_needed] 
    
        num_full_batches = total_needed // BATCH_SIZE
        remaining_questions = total_needed % BATCH_SIZE
        
        for batch_num in range(num_full_batches):
            if remaining_to_generate <= 0:
                break
                
            current_batch_size = min(BATCH_SIZE, remaining_to_generate)
            logger.info(f"Processing batch {batch_num + 1}/{num_full_batches} for {skill} ({current_batch_size} questions)")
            
            batch = QuestionBatch(
                skill=skill,
                context=context,
                target_count=current_batch_size,
                difficulty_distribution=difficulty_distribution
            )
            
            batch_questions = []
            for attempt in range(MAX_RETRIES):
                if current_batch_size <= 0:
                    break
                    
                batch.target_count = current_batch_size
                current_batch = await self._generate_batch_questions(batch)
                questions_to_add = current_batch[:current_batch_size]
                batch_questions.extend(questions_to_add)
                current_batch_size -= len(questions_to_add)
                
                if current_batch_size <= 0:
                    break
                    
            all_questions.extend(batch_questions)
            remaining_to_generate -= len(batch_questions)
            logger.info(f"Batch {batch_num + 1} complete. Total questions so far: {len(all_questions)}")
        
        if remaining_questions > 0 and remaining_to_generate > 0:
            final_batch = QuestionBatch(
                skill=skill,
                context=context,
                target_count=remaining_to_generate,
                difficulty_distribution=difficulty_distribution
            )
            
            final_questions = []
            for attempt in range(MAX_RETRIES):
                if remaining_to_generate <= 0:
                    break
                    
                final_batch.target_count = remaining_to_generate
                current_batch = await self._generate_batch_questions(final_batch)
                questions_to_add = current_batch[:remaining_to_generate]
                final_questions.extend(questions_to_add)
                remaining_to_generate -= len(questions_to_add)
                
                if remaining_to_generate <= 0:
                    break
                    
            all_questions.extend(final_questions)
        
        logger.info(f"Completed question generation for {skill}. Total valid questions: {len(all_questions)}/{total_needed}")
        return all_questions[:total_needed]  

    async def generate_questions(self, skill_contexts: Dict[str, Dict], params: Dict) -> List[Dict]:
        """
        Generate questions for all skills using their contexts in parallel.
        
        Args:
            skill_contexts: Context information for each skill
            params: Generation parameters
            
        Returns:
            List of generated questions
        """
        total_questions = params['total_questions']
        skills = list(skill_contexts.keys())
        difficulty_dist = params['difficulty_distribution']
        
        base_questions_per_skill = total_questions // len(skills)
        extra_questions = total_questions % len(skills)
        target_counts = {
            skill: base_questions_per_skill + (1 if i < extra_questions else 0)
            for i, skill in enumerate(skills)
        }
        
        tasks = [
            self._generate_questions_for_skill(
                skill,
                skill_contexts[skill],
                target_counts[skill],
                difficulty_dist
            )
            for skill in skills
        ]
        
        skill_results = await asyncio.gather(*tasks)
        all_questions = [q for skill_questions in skill_results for q in skill_questions]
        
        total_generated = len(all_questions)
        if total_generated < total_questions:
            logger.warning(f"Generated {total_generated}/{total_questions} questions. Attempting to generate missing questions.")
            
            missing_distribution = {
                skill: target_counts[skill] - len([q for q in all_questions if q.get('category') == skill])
                for skill in skills
            }
            
            missing_tasks = [
                self._generate_questions_for_skill(
                    skill,
                    skill_contexts[skill],
                    needed,
                    difficulty_dist
                )
                for skill, needed in missing_distribution.items()
                if needed > 0
            ]
            
            if missing_tasks:
                additional_results = await asyncio.gather(*missing_tasks)
                remaining_needed = total_questions - len(all_questions)
                additional_questions = []
                for skill_questions in additional_results:
                    if remaining_needed <= 0:
                        break
                    # Take up to remaining_needed from this skill's questions
                    take = min(remaining_needed, len(skill_questions))
                    additional_questions.extend(skill_questions[:take])
                    remaining_needed -= take
                all_questions.extend(additional_questions)
        
        logger.info(f"Final question count: {len(all_questions)}/{total_questions}")
        return all_questions  

    def clean_text(self, text: str) -> str:
        """
        Clean text by removing problematic characters.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        try:
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
            text = text.replace('\ufffd', '')
            
            text = re.sub(r'[\uD800-\uDFFF]', '', text)
            
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)
            text = text.strip()
            
            return text
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return ''.join(c for c in text if ord(c) < 128)
    
    def aggregate_skill_content(self, input_data: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """
        Aggregates content for each skill into a single string while preserving other fields.
        
        Args:
            input_data: Input data with skills as keys
            
        Returns:
            Transformed data with concatenated content for each skill
        """
        result = {}
        
        for skill, entries in input_data.items():
            aggregated = {
                'urls': [],
                'titles': [],
                'snippets': [],
                'content': '',
                'category': entries[0].get('category', '') if entries else ''
            }
            
            for entry in entries:
                if entry.get('url'):
                    aggregated['urls'].append(entry['url'])
                if entry.get('title'):
                    aggregated['titles'].append(self.clean_text(entry['title']))
                if entry.get('snippet'):
                    aggregated['snippets'].append(self.clean_text(entry['snippet']))
                if entry.get('content'):
                    if aggregated['content']:
                        aggregated['content'] += ' '
                    aggregated['content'] += self.clean_text(entry['content'])
            
            result[skill] = aggregated        
        return result
    
async def generate_assessment(skills, duration, difficulty, total_questions, chat_id, user_id):
    """
    Generate assessment questions based on provided skills and parameters.
    
    Args:
        skills (list): List of skills to test
        duration (int): Test duration in hours
        difficulty (str): Test difficulty level
        total_questions (int): Total number of questions to generate
        job_description (str): Job description text or Optional
        
    Returns:
        tuple: (generated_questions, time_taken)
    """
    generation_start_time = time.time()
    
    generator = ContextBasedQuestionGenerator()
    test_planner = TestPlanner()
    retriever = SkillContextRetriever()
    
    config = TestConfig(
        duration=duration,
        difficulty=difficulty,
        skills=skills,
        job_description=None,
        total_questions=total_questions  
    )
    
    # Calculate test parameters
    params = test_planner.calculate_test_parameters(config)
    print("\nTest parameters:")
    print(f"Total questions: {params['total_questions']}")
    print(f"Skills to test: {', '.join(params['skills'])}")
    print(f"Difficulty distribution: {params['difficulty_distribution']}")
   
    print("\nRetrieving skill contexts...")
    skill_contexts = retriever.get_skill_context(params['skills'], params['total_questions'])
    
    for skill in params['skills']:
        # Normalize skill name (trim whitespace)
        normalized_skill = skill.strip()
        if normalized_skill not in skill_contexts:
            print(f"Warning: No context found for skill '{normalized_skill}'. Creating empty context.")
           
            skill_contexts[normalized_skill] = [
                {
                    'url': '',
                    'title': f'{normalized_skill} concepts',
                    'snippet': '',
                    'content': f'Generate questions about {normalized_skill} based on standard industry knowledge.',
                    'category': 'technical'  # Default to technical category
                }
            ]
    
    with open("contexts.json", "w", encoding="utf-8") as f:
        json.dump(skill_contexts, f, indent=4)

    aggregated_contexts = generator.aggregate_skill_content(skill_contexts)
    with open("aggr_contexts.json", "w", encoding="utf-8") as f:
        json.dump(aggregated_contexts, f, indent=4)   
    
    # Generate questions
    print("\nGenerating questions...")
    questions = await generator.generate_questions(aggregated_contexts, params)
    
    # Save questions to file
    with open('generated_questions5.json', 'w') as f:
        json.dump(questions, f, indent=2)
    
    # Prepare metadata for MongoDB
    metadata = {
        'total_questions': params['total_questions'],
        'difficulty_level': config.difficulty,
        'generation_date': datetime.utcnow().isoformat(),
        'skills': list(aggregated_contexts.keys()),
        'job_description': config.job_description
    }

    mongo_handler = MongoDBHandler()
    try:
        await mongo_handler.insert_questions(questions, metadata,chat_id, user_id)
        logger.info(f"Successfully saved {len(questions)} questions to MongoDB")
    except Exception as e:
        logger.error(f"Failed to save questions to MongoDB: {str(e)}")
        print(f"Error saving to MongoDB: {str(e)}")
    
    generation_end_time = time.time()
    generation_time = generation_end_time - generation_start_time
    
    return questions, generation_time
async def main():
    """Main function to run the question generation process."""
    start_time = time.time()
    
    
    # Default parameters
    duration = 3
    difficulty = 'medium'
    final_skills = ['python', 'machine learning', 'deep learning', 'computer vision', 'nlp', 'fastapi', 'llm fine-tuning', 'reinforcement learning', 'transformer models', 'database management']

    total_questions = 300
#     job_description = '''About the job
# Our Company

# Changing the world through digital experiences is what Adobe's all about. We give everyone—from emerging artists to global brands—everything they need to design and deliver exceptional digital experiences! We're passionate about empowering people to create beautiful and powerful images, videos, and apps, and transform how companies interact with customers across every screen.

# We're on a mission to hire the very best and are committed to creating exceptional employee experiences where everyone is respected and has access to equal opportunity. We realize that new ideas can come from everywhere in the organization, and we know the next big idea could be yours!

# The Opportunity

# Are you ready to challenge the norms of technology and innovation? Adobe is searching for a Computer Scientist - 1 to join our exceptional Information Technology team. This is a groundbreaking opportunity to collaborate with a team of established authorities dedicated to delivering flawless digital experiences. You'll be at the forefront of developing innovative solutions that impact millions of users globally.

# What You'll Do

# Collaborate with cross-functional teams to craft and implement innovative IT solutions that drive business success. 
# Develop and maintain scalable software applications, ensuring they meet the highest standards of performance and security. 
# Perform detailed testing and debugging to ensure flawless operation and user experience. 
# Stay ahead of industry trends to determine the most effective technologies and methodologies for our projects. 
# Provide technical guidance and mentorship to junior team members, encouraging an inclusive and collaborative environment. 

# What you need to succeed

# Degree in Computer Science, Information Technology, or equivalent experience in the field. 
# Demonstrated expertise in programming languages such as Java, Python, or C++. 
# Proven ability to develop and implement software solutions that compete in a fast-paced environment. 
# Strong problem-solving skills and the ability to think critically and creatively. 
# Excellent communication skills, with the ability to explain complex technical concepts to non-technical collaborators. 
# A passionate and ambitious attitude, with a dedication to continuous learning and improvement. 

# Adobe is proud to be an Equal Employment Opportunity and affirmative action employer. We do not discriminate based on gender, race or color, ethnicity or national origin, age, disability, religion, sexual orientation, gender identity or expression, veteran status, or any other applicable characteristics protected by law. Learn more.

# Adobe aims to make Adobe.com accessible to any and all users. If you have a disability or special need that requires accommodation to navigate our website or complete the application process, email accommodations@adobe.com or call (408) 536-3015.

# Adobe values a free and open marketplace for all employees and has policies in place to ensure that we do not enter into illegal agreements with other companies to not recruit or hire each other's employees.



# '''

    questions, generation_time = await generate_assessment(
        final_skills, 
        duration, 
        difficulty, 
        total_questions
    )
    
    print(f"\nGenerated {len(questions)} questions")
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.2f} seconds")
    print(f"Question generation time: {generation_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())