import type { VercelRequest, VercelResponse } from '@vercel/node';

const termsHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - Discord RAG Bot</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #5865F2;
            border-bottom: 3px solid #5865F2;
            padding-bottom: 10px;
        }
        h2 {
            color: #5865F2;
            margin-top: 30px;
        }
        .last-updated {
            color: #666;
            font-style: italic;
            margin-bottom: 30px;
        }
        a {
            color: #5865F2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Terms of Service</h1>
        <p class="last-updated">Last Updated: ${new Date().toLocaleDateString()}</p>

        <h2>1. Acceptance of Terms</h2>
        <p>By using this Discord bot (the "Bot"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, please do not use the Bot.</p>

        <h2>2. Description of Service</h2>
        <p>The Bot is an automated support assistant that uses Retrieval-Augmented Generation (RAG) technology and artificial intelligence to provide responses to user inquiries in Discord forum channels. The Bot is designed to assist with support-related questions and provide information from a knowledge base.</p>

        <h2>3. Use of the Bot</h2>
        <p>You agree to use the Bot only for lawful purposes and in accordance with these Terms. You agree not to:</p>
        <ul>
            <li>Use the Bot in any way that violates Discord's Terms of Service or Community Guidelines</li>
            <li>Attempt to exploit, abuse, or harm the Bot or its underlying systems</li>
            <li>Use the Bot to generate or distribute harmful, offensive, or illegal content</li>
            <li>Interfere with or disrupt the Bot's operation</li>
            <li>Attempt to reverse engineer or extract the Bot's source code or data</li>
        </ul>

        <h2>4. AI-Generated Content</h2>
        <p>The Bot uses artificial intelligence to generate responses. While we strive for accuracy, AI-generated content may contain errors or inaccuracies. The Bot's responses are provided "as is" and should not be considered as professional advice unless explicitly stated.</p>

        <h2>5. Data Collection and Privacy</h2>
        <p>Your use of the Bot is subject to our Privacy Policy. By using the Bot, you consent to the collection and use of information as described in the Privacy Policy.</p>

        <h2>6. Availability and Modifications</h2>
        <p>We reserve the right to:</p>
        <ul>
            <li>Modify, suspend, or discontinue the Bot at any time</li>
            <li>Update these Terms at any time</li>
            <li>Restrict access to the Bot for any user who violates these Terms</li>
        </ul>
        <p>We will make reasonable efforts to notify users of significant changes to the Bot or these Terms.</p>

        <h2>7. Limitation of Liability</h2>
        <p>THE BOT IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED. WE DISCLAIM ALL WARRANTIES, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.</p>
        <p>WE SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING OUT OF YOUR USE OF OR INABILITY TO USE THE BOT.</p>

        <h2>8. Intellectual Property</h2>
        <p>All content, features, and functionality of the Bot, including but not limited to text, graphics, logos, and software, are the property of the Bot's operators and are protected by copyright, trademark, and other intellectual property laws.</p>

        <h2>9. Termination</h2>
        <p>We reserve the right to terminate or suspend your access to the Bot immediately, without prior notice, for any violation of these Terms or for any other reason we deem necessary.</p>

        <h2>10. Governing Law</h2>
        <p>These Terms shall be governed by and construed in accordance with applicable laws, without regard to conflict of law provisions.</p>

        <h2>11. Contact Information</h2>
        <p>If you have any questions about these Terms, please contact us through the Discord server where the Bot is deployed.</p>

        <h2>12. Severability</h2>
        <p>If any provision of these Terms is found to be unenforceable or invalid, that provision shall be limited or eliminated to the minimum extent necessary, and the remaining provisions shall remain in full force and effect.</p>
    </div>
</body>
</html>`;

export default function handler(_req: VercelRequest, res: VercelResponse) {
  res.setHeader('Content-Type', 'text/html');
  res.setHeader('Cache-Control', 'public, max-age=3600'); // Cache for 1 hour
  return res.status(200).send(termsHTML);
}

