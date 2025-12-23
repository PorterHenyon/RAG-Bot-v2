# Discord Bot Verification - Terms of Service & Privacy Policy Guide

## ✅ What's Been Created

I've created two API routes that serve your Terms of Service and Privacy Policy:

1. **Terms of Service**: `/api/terms`
2. **Privacy Policy**: `/api/privacy`

These are accessible as HTML pages that Discord can verify.

## 🔗 Your Links

After deploying to Vercel, your links will be:

- **Terms of Service**: `https://your-vercel-url.vercel.app/api/terms`
- **Privacy Policy**: `https://your-vercel-url.vercel.app/api/privacy`

**Replace `your-vercel-url` with your actual Vercel deployment URL** (e.g., `rag-bot-v2.vercel.app`)

## 📝 How to Link Them in Discord Developer Portal

### Step 1: Deploy to Vercel

1. Push your code to GitHub (if not already done)
2. Make sure Vercel auto-deploys, or manually redeploy
3. Wait for deployment to complete
4. Note your Vercel URL (e.g., `https://rag-bot-v2.vercel.app`)

### Step 2: Test the Links

Before submitting, test that the links work:

```bash
# Test Terms of Service
curl https://your-vercel-url.vercel.app/api/terms

# Test Privacy Policy
curl https://your-vercel-url.vercel.app/api/privacy
```

Or simply open them in your browser:
- `https://your-vercel-url.vercel.app/api/terms`
- `https://your-vercel-url.vercel.app/api/privacy`

You should see nicely formatted HTML pages.

### Step 3: Submit in Discord Developer Portal

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot application
3. Navigate to **"Bot"** section in the left sidebar
4. Scroll down to find the **"Bot Verification"** section
5. You should see fields for:
   - **Terms of Service URL**
   - **Privacy Policy URL**
6. Enter your URLs:
   - **Terms of Service URL**: `https://your-vercel-url.vercel.app/api/terms`
   - **Privacy Policy URL**: `https://your-vercel-url.vercel.app/api/privacy`
7. Click **"Save Changes"** or **"Submit for Verification"**

## ✅ Requirements Checklist

Discord requires that your Terms of Service and Privacy Policy:

- ✅ Are publicly accessible (no authentication required)
- ✅ Are served over HTTPS
- ✅ Are in a readable format (HTML is perfect)
- ✅ Are accessible via direct URL (not behind a redirect)
- ✅ Contain relevant information about your bot

All of these requirements are met by the pages we created!

## 🔍 What's Included

### Terms of Service includes:
- Acceptance of terms
- Description of service
- Use restrictions
- AI-generated content disclaimer
- Data collection notice
- Availability and modifications
- Limitation of liability
- Intellectual property
- Termination
- Contact information

### Privacy Policy includes:
- Information collection
- How data is used
- Data storage and retention
- Data sharing policies
- Third-party services
- User rights (GDPR/CCPA compliant)
- Security measures
- Contact information

## 🎨 Customization (Optional)

If you want to customize the Terms of Service or Privacy Policy:

1. Edit `api/terms.ts` for Terms of Service
2. Edit `api/privacy.ts` for Privacy Policy
3. Modify the HTML content in the `termsHTML` or `privacyHTML` variables
4. Redeploy to Vercel

## 🚨 Important Notes

- **Make sure your Vercel deployment is live** before submitting the links
- **Test the links** in an incognito/private browser window to ensure they're publicly accessible
- **Keep the pages updated** - Discord may check them periodically
- **The pages are cached for 1 hour** - if you update them, changes may take up to an hour to appear

## 📞 Need Help?

If Discord rejects your links:
1. Verify the URLs are accessible (open in incognito browser)
2. Check that they return HTML (not JSON or error pages)
3. Ensure they're served over HTTPS
4. Make sure the content is relevant to your bot

## 🎉 After Verification

Once Discord approves your bot verification:
- Your bot can be used in more servers
- You may have access to additional features
- Your bot will appear verified in Discord

---

**Quick Reference:**
- Terms: `https://your-vercel-url.vercel.app/api/terms`
- Privacy: `https://your-vercel-url.vercel.app/api/privacy`

