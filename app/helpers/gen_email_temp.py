def forgot_password_template(otp: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reset Your Password</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 50px auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
            .header {{ text-align: center; font-size: 24px; margin-bottom: 20px; }}
            .otp {{ font-size: 22px; font-weight: bold; text-align: center; background: #e3f2fd; padding: 10px; border-radius: 5px; display: inline-block; }}
            .footer {{ margin-top: 20px; font-size: 14px; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Password Reset Request</div>
            <p>Hello,</p>
            <p>You requested to reset your password. Use the OTP below to proceed:</p>
            <p class="otp">{otp}</p>
            <p>If you did not request this, please ignore this email.</p>
            <div class="footer">&copy; 2025 Your Company. All rights reserved.</div>
        </div>
    </body>
    </html>
    """