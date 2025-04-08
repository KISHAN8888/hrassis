import os
import json
import time
import re
import numpy as np
import requests
from typing import List, Dict, Literal, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import logging
from pydantic import BaseModel, RootModel
from dataclasses import dataclass
load_dotenv()



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@dataclass
class TestConfig:
    duration: int 
    difficulty: str  # 'easy', 'moderate', 'hard'
    skills: List[str]
    job_description: Optional[str] = None
    total_questions: int = None 

class TestPlanner:
    def __init__(self):
        self.time_per_question = {
            'easy': 45, 
            'moderate': 75,
            'hard': 90
        }
        self.difficulty_distribution = {
            "easy": {"easy": 0.7, "moderate": 0.3, "hard": 0},
            "medium": {"easy": 0.2, "moderate": 0.6, "hard": 0.2},
            "hard": {"easy": 0, "moderate": 0.3, "hard": 0.7}
        }
        self.max_skills_per_hour = 10  # Maximum skills to test per hour
        self.max_total_skills = 15
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def calculate_test_parameters(self, config: TestConfig) -> Dict:
        
        total_questions =config.total_questions


        adjusted_skills = self._validate_skills(config.skills)
        
        # Calculate questions per skill based on total questions
        questions_per_skill = total_questions // len(adjusted_skills)
        
        # Adjust for any remaining questions
        remaining_questions = total_questions % len(adjusted_skills)
        questions_distribution = [questions_per_skill + (1 if i < remaining_questions else 0) 
                                for i in range(len(adjusted_skills))]
        
        return {
            'total_questions': total_questions,
            'questions_per_skill': questions_distribution,
            'skills': adjusted_skills,
            'difficulty_distribution': self.difficulty_distribution[config.difficulty]
        }


    def _validate_skills(self, skills: List[str]) -> List[str]:
        """Validate and limit the number of skills if necessary"""
        max_allowed_skills = self.max_total_skills
        return skills[:max_allowed_skills]

class SkillContextRetriever:
    def __init__(self, openai_api_key: str = None, searxng_url: str = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        self.searxng_url = searxng_url or os.getenv('SEARXNG_URL', 'http://64.227.185.185:8080/search')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        
        self.embedding_cache = {}
        
        self.domain_preferences = {
            'technical': [
                'geeksforgeeks.org',
                'stackoverflow.com',
                'github.com',
                'leetcode.com',
                'hackerrank.com',
                'dev.to',
                'datacamp.com',
                'interviewbit.com'
            ],
            'non_technical': [
                'forbes.com',
                'hbr.org',
                'mindtools.com'
            ]
        }
    def generate_search_queries(self, skills: List[str], questions_per_skill: int) -> Dict:
        """
        Generate search queries for all skills at once using OpenAI structured response
        Returns: {
            "skill1": {"query": "query1", "category": "technical"},
            "skill2": {"query": "query2", "category": "non_technical"},
            ...
        }
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                prompt = f"""
                For each skill in this list: {skills}
                Generate one specific search query to find mcq assessment questions don't specify the number of questions.
                For each skill also determine if it is 'technical' or 'non_technical'.
                
                Note: Generate more specific queries for skills that need {questions_per_skill} questions.
                """
                
                # Define models for structured output - using a list approach
                class SkillQueryItem(BaseModel):
                    skill_name: str
                    query: str
                    category: Literal["technical", "non_technical"]
                
                class QueryList(BaseModel):
                    queries: List[SkillQueryItem]
                
                # Make the structured-output call
                response = self.openai_client.beta.chat.completions.parse(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    response_format=QueryList
                )
               
                queries_list = response.choices[0].message.parsed.queries
                queries_dict = {item.skill_name: {"query": item.query, "category": item.category} 
                               for item in queries_list}
                print(queries_dict)
                
                return queries_dict
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise Exception(f"Failed to generate queries after {max_retries} attempts. Last error: {str(e)}")
                print(f"Query generation failed (attempt {retry_count}/{max_retries}): {str(e)}")
                continue
    
    def search_skill(self, query: str, category: str) -> List[Dict]:
        """Perform web search using SearXNG for a specific query"""
        print(f"Searching SearXNG for: {query}")
        
        if category == 'technical':
            return self.search_searxng(query, num_results=10, engines='google,geeksforgeeks,tpointtech')
        else:
            return self._original_search(query, category)
    
    def search_searxng(self, query, num_results=10, engines=None):
        """
        Search SearXNG and return the top results
        
        Parameters:
        query (str): The search query
        num_results (int): Number of results to return
        engines (list or str): Specific engine(s) to use for the search. If None, uses a mix of general and custom engines.
        
        Returns:
        list: Top search results
        """
        if engines is None:
            engines = 'google,duckduckgo,bing,geeksforgeeks'
        elif isinstance(engines, list):
            engines = ','.join(engines)
        params = {
            'q': query,
            'format': 'json',
            'categories': 'general, technical', 
            'engines': engines,
            'language': 'en',
            'pageno': 1,
            'results_count': num_results
        }
        
        try:
            response = self.session.get(self.searxng_url, params=params, timeout=10)
            response.raise_for_status()  
            
            results_json = response.json()
            results = results_json.get('results', [])[:num_results]
            
            valid_items = []
            for item in results:
                if 'url' in item and 'title' in item:
                    valid_item = {
                        'link': item['url'],
                        'title': item['title'],
                        'snippet': item.get('content', ''),
                        'engine': item.get('engine', '')
                    }
                    valid_items.append(valid_item)
            
            ranked_results = self.rank_results_by_heuristics(valid_items, query, 'technical')
            return ranked_results[:5] 
        
        except requests.exceptions.RequestException as e:
            print(f"Error searching SearXNG: {e}")
            return []

    def _original_search(self, query: str, category: str) -> List[Dict]:
        """Original search method for non-technical skills"""

        params = {
            'q': query,
            'format': 'json',
            'language': 'en',
            'pageno': 1,
            'results_count': 10
        }
        
        try:
            response = self.session.get(self.searxng_url, params=params, timeout=10)
            if response.status_code == 200:
                response_json = response.json()
                
                if 'results' not in response_json:
                    print(f"No results found in response. Response keys: {response_json.keys()}")
                    return []
                    
                items = response_json.get('results', [])
                items = items[:10]
                
                valid_items = []
                for item in items:
                    if 'url' in item and 'title' in item:
                        valid_item = {
                            'link': item['url'],
                            'title': item['title'],
                            'snippet': item.get('content', ''),
                            'engine': item.get('engine', '')
                        }
                        valid_items.append(valid_item)
                
                ranked_results = self.rank_results_by_heuristics(valid_items, query, category)
                return ranked_results[:5]
            else:
                print(f"SearXNG API returned error code: {response.status_code}")
                print(f"Response content: {response.text}")
                return []
        except Exception as e:
            print(f"Error searching for query {query}: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using OpenAI's embeddings API with caching"""
        try:
            if not text.strip():
                return None
                
            response = self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"  
            )
            embedding = response.data[0].embedding
        
            
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None
        
    def rank_results_by_heuristics(self, results: List[Dict], query: str, category: str) -> List[Dict]:
        """Rank search results by simple heuristics instead of embeddings"""
        if not results:
            return []
        
        query_terms = set(query.lower().split())
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about'}
        query_terms = {term for term in query_terms if term not in common_words}
        
        scored_results = []
        
        for result in results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            url = result.get('link', '').lower()
            
            title_matches = sum(1 for term in query_terms if term in title)
            snippet_matches = sum(1 for term in query_terms if term in snippet)
            
            keyword_score = (title_matches * 3 + snippet_matches) / max(1, len(query_terms))
            
            domain = urlparse(result.get('link', '')).netloc
            category_domains = self.domain_preferences.get(category, [])
            
            domain_bonus = 0.3 if any(preferred in domain for preferred in category_domains) else 0
            
            
            final_score = keyword_score + domain_bonus 
            
            scored_results.append((final_score, result))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [result for _, result in scored_results]    

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not a or not b:
            return 0
            
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _rank_results_by_embedding(self, results: List[Dict], query: str, category) -> List[Dict]:
        """
        Rank search results by embedding similarity to query
        """
        if not results:
            return []
        
        # Get embedding for the query
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            print("Warning: Could not get embedding for query. Falling back to default ranking.")
            return results[:5]
        
        scored_results = []
        
        # Batch process embeddings for efficiency
        texts_to_embed = []
        for result in results:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            combined_text = f"{title} {snippet}"
            texts_to_embed.append((combined_text, result))
        
        # Process in smaller batches
        batch_size = 5
        for i in range(0, len(texts_to_embed), batch_size):
            batch = texts_to_embed[i:i+batch_size]
            batch_texts = [text for text, _ in batch]
            
            # Get embeddings for all texts in this batch
            for j, (text, result) in enumerate(batch):
                result_embedding = self._get_embedding(text)
                if not result_embedding:
                    continue
                    
                similarity = self._cosine_similarity(query_embedding, result_embedding)
          
                
                domain = urlparse(result.get('link', '')).netloc
                category_domains = self.domain_preferences.get(category, [])
                
                domain_bonus = 0.1 if any(preferred in domain for preferred in category_domains) else 0

              
                final_score = similarity + domain_bonus
                
                scored_results.append((final_score, result))
        
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return the top results
        return [result for _, result in scored_results]

    def _extract_content_worker(self, url_data):
        """Worker function for parallel content extraction"""
        url, title, snippet, category = url_data
        content = self._extract_content(url)
        
        if content:
            return {
                'url': url,
                'title': title,
                'snippet': snippet,
                'content': content,
                'category': category
            }
        return None
    
    def get_skill_context(self, skills: List[str], questions_per_skill: int) -> Dict[str, List[Dict]]:
        """Main method to get context for all skills with parallel processing"""
        queries_data = self.generate_search_queries(skills, questions_per_skill)
        
        skill_contexts = {}
        
        with ThreadPoolExecutor(max_workers=min(len(skills), 5)) as executor:
            futures = {}
            
            for skill, data in queries_data.items():
                print(f"Searching for context about: {skill}")
                query = data['query']
                category = data['category']
                
                future = executor.submit(self.search_skill, query, category)
                futures[future] = (skill, category)
            
            search_results = {}
            for future in as_completed(futures):
                skill, category = futures[future]
                try:
                    results = future.result()
                    if results:
                        search_results[skill] = (results, category)
                except Exception as e:
                    print(f"Error processing skill {skill}: {str(e)}")
        
        # Parallel content extraction for all URLs
        url_data_list = []
        for skill, (results, category) in search_results.items():
            for result in results:
                url = result.get('link', '')
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                url_data_list.append((url, title, snippet, category, skill))
        
        # Process URL content extraction in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            
            for url_data in url_data_list:
                url, title, snippet, category, skill = url_data
                future = executor.submit(self._extract_content_worker, (url, title, snippet, category))
                futures[future] = skill
            
            # Collect extraction results
            for future in as_completed(futures):
                skill = futures[future]
                try:
                    result = future.result()
                    if result:
                        if skill not in skill_contexts:
                            skill_contexts[skill] = []
                        skill_contexts[skill].append(result)
                except Exception as e:
                    print(f"Error extracting content for skill {skill}: {str(e)}")
        
        return skill_contexts

    def _extract_content(self, url: str) -> str:
        """
        Extract meaningful content from a webpage with improved extraction capabilities.
        
        Args:
            url: The URL of the webpage to extract content from
            
        Returns:
            Extracted text content from the webpage
        """
        try:
            # Fetch the webpage with timeout
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Raise exception for 4XX/5XX status codes
            
            # Handle different content types
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/pdf' in content_type:
                return "PDF content detected - content extraction skipped"
            if not ('text/html' in content_type or 'application/xhtml+xml' in content_type):
                return f"Unsupported content type: {content_type}"
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements that typically contain non-content
            for element in soup.select('script, style, nav, footer, header, aside, [class*="ads"], [class*="banner"], iframe, .comments, #comments'):
                element.decompose()
            
            # Try to find main content using common content containers
            main_content = None
            
            # 1. Look for schema.org Article markup
            article = soup.find(['div', 'article'], attrs={'itemtype': 'http://schema.org/Article'})
            if article:
                main_content = article
            
            # 2. Look for article, main or standard content divs
            if not main_content:
                content_selectors = [
                    'article', 'main', 
                    '[role="main"]',
                    '[id*="content-main"]', '[class*="content-main"]',
                    '[id*="main-content"]', '[class*="main-content"]',
                    'div[class*="article"]', 'div[id*="article"]',
                    'div[class*="post"]', 'div[id*="post"]',
                    'div[class*="content"]', 'div[id*="content"]'
                ]
                for selector in content_selectors:
                    main_content = soup.select_one(selector)
                    if main_content and len(main_content.get_text(strip=True)) > 200:
                        break
            
            # Process content
            if main_content and len(main_content.get_text(strip=True)) > 200:
                # Extract from identified main content
                content_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'ul', 'ol', 'pre', 'code', 'blockquote'])
            else:
                # Fallback: Use density analysis to find content-rich areas
                paragraphs = soup.find_all('p')
                content_elements = [p for p in paragraphs if len(p.get_text(strip=True)) > 20]
                
                # If still no substantial content, get all potentially useful elements
                if not content_elements or sum(len(p.get_text(strip=True)) for p in content_elements) < 200:
                    content_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'ul', 'ol', 'pre', 'code', 'blockquote'])
            
            # Build structured content with heading hierarchy preserved
            extracted_content = []
            for elem in content_elements:
                if elem.name.startswith('h') and len(elem.get_text(strip=True)) > 0:
                    # Add newlines around headings for better formatting
                    extracted_content.append("\n\n" + elem.get_text(strip=True) + "\n")
                elif elem.name in ['ul', 'ol']:
                    # Handle lists
                    list_items = []
                    for li in elem.find_all('li'):
                        item_text = li.get_text(strip=True)
                        if item_text:
                            list_items.append(f"• {item_text}")
                    extracted_content.append("\n" + "\n".join(list_items) + "\n")
                elif elem.name == 'blockquote':
                    # Format blockquotes
                    quote_text = elem.get_text(strip=True)
                    if quote_text:
                        extracted_content.append(f"\n> {quote_text}\n")
                else:
                    # Regular paragraph or other element
                    text = elem.get_text(strip=True)
                    if text and len(text) > 1:
                        extracted_content.append(text)
            
            # Join all content and clean up
            text = "\n\n".join(extracted_content)
            
            # Clean up whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)  # Replace 3+ newlines with 2
            text = re.sub(r' {2,}', ' ', text)      # Replace 2+ spaces with 1
            
            return self._clean_content(text)
            
        except requests.exceptions.Timeout:
            return "Error: Request timed out"
        except requests.exceptions.TooManyRedirects:
            return "Error: Too many redirects"
        except requests.exceptions.RequestException as e:
            return f"Error: Failed to retrieve the webpage: {str(e)}"
        except Exception as e:
            return f"Error: Content extraction failed: {str(e)}"
    
    def _clean_content(self, content: str) -> str:
        """Clean extracted content to remove gibberish"""
        if not content:
            return ""
            
        # Remove Unicode escape sequences that often appear as gibberish
        content = re.sub(r'\\u[0-9a-fA-F]{4,}', ' ', content)
        
        # Remove non-printable characters
        content = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', content)
        
        # Normalize whitespace
        content = ' '.join(content.split())
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        
        # Keep only sentences with reasonable length and mostly alphanumeric characters
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip if too short
            if len(sentence.split()) < 3:
                continue
                
            # Skip very long sentences
            if len(sentence.split()) > 50:
                continue
                
            # Check for gibberish: ratio of alphanumeric to total characters
            alpha_ratio = sum(c.isalnum() or c.isspace() for c in sentence) / max(1, len(sentence))
            if alpha_ratio < 0.7:  # At least 70% should be alphanumeric or spaces
                continue
                
            clean_sentences.append(sentence)
        
        # Reassemble with proper punctuation
        clean_text = '. '.join(clean_sentences)
        if clean_text and not clean_text.endswith(('.', '!', '?')):
            clean_text += '.'
            
        return clean_text

def calculate_test_parameters(duration: int, difficulty: str, skills: List[str]) -> Dict:
    """Calculate test parameters based on duration and difficulty"""
    time_per_question = {
        'easy': 45,
        'moderate': 75,
        'hard': 90
    }
    
    avg_time = time_per_question[difficulty]
    total_questions = (duration * 3600) // avg_time
    
    return {
        'questions_per_skill': max(1, total_questions // len(skills)),
        'total_questions': total_questions
    }

# Example usage
if __name__ == "__main__":
    # Initialize the retriever with SearXNG URL
    start_time = time.time()
    searxng_url = os.getenv('SEARXNG_URL', 'http://64.227.185.185:8080/search')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    retriever = SkillContextRetriever(openai_api_key=openai_api_key, searxng_url=searxng_url)
    
    # Example: search for a skill
    skills = ["javascript", "reactjs","c programming", "Data strucutres and Algorithms", "DBMS","Rest API","System design", "RAG","Pytorch","tensorflow"]
    test_params = calculate_test_parameters(duration=1, difficulty="moderate", skills=skills)
    skill_contexts = retriever.get_skill_context(skills, test_params['questions_per_skill'])
    
    with open("new_contexts.json", "w", encoding="utf-8") as f:
        json.dump(skill_contexts, f, indent=4)

    end_time = time.time()
    tot =end_time -start_time
    print(f"total time {tot}")    