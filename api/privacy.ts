import type { VercelRequest, VercelResponse } from '@vercel/node';

const privacyHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - Discord RAG Bot</title>
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
        <h1>Privacy Policy</h1>
        <p class="last-updated">Last Updated: ${new Date().toLocaleDateString()}</p>

        <h2>1. Introduction</h2>
        <p>This Privacy Policy describes how we collect, use, and protect information when you use our Discord bot (the "Bot"). By using the Bot, you agree to the collection and use of information in accordance with this policy.</p>

        <h2>2. Information We Collect</h2>
        <p>The Bot may collect and process the following types of information:</p>
        
        <h3>2.1 Discord User Information</h3>
        <ul>
            <li>Discord user ID</li>
            <li>Discord username and discriminator</li>
            <li>Server membership information (when the Bot is used in a server)</li>
        </ul>

        <h3>2.2 Message Content</h3>
        <ul>
            <li>Forum post content and titles</li>
            <li>Messages sent in channels where the Bot is active</li>
            <li>Thread conversations and replies</li>
        </ul>

        <h3>2.3 Usage Data</h3>
        <ul>
            <li>Interactions with the Bot (commands used, responses generated)</li>
            <li>Forum post status (solved, unsolved, pending)</li>
            <li>Timestamps of interactions</li>
        </ul>

        <h2>3. How We Use Information</h2>
        <p>We use the collected information for the following purposes:</p>
        <ul>
            <li><strong>Providing Support Services:</strong> To respond to forum posts and provide automated support responses</li>
            <li><strong>Improving the Bot:</strong> To analyze interactions and improve response quality</li>
            <li><strong>Knowledge Base Management:</strong> To create and maintain a knowledge base of solutions (with appropriate anonymization)</li>
            <li><strong>Bot Functionality:</strong> To enable features such as RAG (Retrieval-Augmented Generation) and auto-responses</li>
        </ul>

        <h2>4. Data Storage</h2>
        <p>Data collected by the Bot is stored securely using cloud storage services (such as Vercel KV, Redis, or similar services). We implement appropriate technical and organizational measures to protect your data against unauthorized access, alteration, disclosure, or destruction.</p>

        <h2>5. Data Retention</h2>
        <p>We retain data for as long as necessary to provide the Bot's services and as required by law. Specifically:</p>
        <ul>
            <li>Active forum posts and conversations are retained while they are active</li>
            <li>Solved forum posts may be retained for a configurable period (typically 30 days) before automatic deletion</li>
            <li>Knowledge base entries (RAG entries) are retained indefinitely to improve the Bot's responses</li>
        </ul>

        <h2>6. Data Sharing</h2>
        <p>We do not sell, trade, or rent your personal information to third parties. We may share information only in the following circumstances:</p>
        <ul>
            <li><strong>Service Providers:</strong> With third-party service providers who assist in operating the Bot (e.g., cloud storage providers, AI service providers)</li>
            <li><strong>Legal Requirements:</strong> When required by law or to protect our rights and safety</li>
            <li><strong>With Consent:</strong> When you have given explicit consent for sharing</li>
        </ul>

        <h2>7. Third-Party Services</h2>
        <p>The Bot uses the following third-party services that may process your data:</p>
        <ul>
            <li><strong>Discord:</strong> The Bot operates within Discord's platform and is subject to Discord's Privacy Policy</li>
            <li><strong>AI Services:</strong> The Bot uses AI services (such as Google Gemini, Groq) to generate responses. These services may process message content to generate responses</li>
            <li><strong>Cloud Storage:</strong> Data is stored using cloud storage providers (Vercel, Redis, etc.)</li>
        </ul>

        <h2>8. Your Rights</h2>
        <p>You have the following rights regarding your data:</p>
        <ul>
            <li><strong>Access:</strong> Request access to the data we hold about you</li>
            <li><strong>Deletion:</strong> Request deletion of your data (subject to legal and operational requirements)</li>
            <li><strong>Correction:</strong> Request correction of inaccurate data</li>
            <li><strong>Opt-Out:</strong> You can stop using the Bot at any time, which will prevent further data collection</li>
        </ul>
        <p>To exercise these rights, please contact us through the Discord server where the Bot is deployed.</p>

        <h2>9. Children's Privacy</h2>
        <p>The Bot is not intended for users under the age of 13. We do not knowingly collect personal information from children under 13. If you are a parent or guardian and believe your child has provided us with personal information, please contact us.</p>

        <h2>10. Security</h2>
        <p>We take reasonable measures to protect your information from unauthorized access, use, or disclosure. However, no method of transmission over the internet or electronic storage is 100% secure, and we cannot guarantee absolute security.</p>

        <h2>11. Changes to This Privacy Policy</h2>
        <p>We may update this Privacy Policy from time to time. We will notify users of any material changes by updating the "Last Updated" date at the top of this policy. Your continued use of the Bot after such changes constitutes acceptance of the updated policy.</p>

        <h2>12. Contact Us</h2>
        <p>If you have any questions about this Privacy Policy or our data practices, please contact us through the Discord server where the Bot is deployed.</p>

        <h2>13. Compliance</h2>
        <p>This Privacy Policy is designed to comply with applicable privacy laws, including GDPR and CCPA where applicable. If you are located in the European Economic Area (EEA), you have additional rights under GDPR, which are outlined in this policy.</p>
    </div>
</body>
</html>`;

export default function handler(_req: VercelRequest, res: VercelResponse) {
  res.setHeader('Content-Type', 'text/html');
  res.setHeader('Cache-Control', 'public, max-age=3600'); // Cache for 1 hour
  return res.status(200).send(privacyHTML);
}

