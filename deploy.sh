#!/bin/bash

# Deployment script for Aptos Comply Agent

echo "🚀 Deploying Aptos Comply Agent..."
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - Aptos Comply Agent"
fi

# Backend Deployment
echo "📦 Backend Deployment Steps:"
echo "1. Push code to GitHub:"
echo "   git remote add origin <your-github-repo-url>"
echo "   git push -u origin main"
echo ""
echo "2. Go to https://render.com"
echo "3. Click 'New +' → 'Blueprint'"
echo "4. Connect your GitHub repository"
echo "5. Render will detect render.yaml and deploy automatically"
echo ""
echo "6. Set these environment variables in Render dashboard:"
echo "   - OPENAI_API_KEY (optional, for AI features)"
echo "   - ONDEMAND_API_KEY=XBKmaTtF167mfnJaEQte41YZbw6zj08S"
echo "   - CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000"
echo ""

# Frontend Deployment
echo "🎨 Frontend Deployment Steps:"
echo "1. Go to https://vercel.com"
echo "2. Click 'New Project'"
echo "3. Import your GitHub repository"
echo "4. Set root directory to 'frontend-next'"
echo "5. Add environment variable:"
echo "   NEXT_PUBLIC_API_URL=https://aptoscomply-backend.onrender.com"
echo "6. Deploy!"
echo ""

# Vercel CLI option
echo "Or use Vercel CLI:"
echo "   cd frontend-next"
echo "   vercel"
echo "   vercel --prod"
echo ""

echo "✅ Deployment configuration files created:"
echo "   - render.yaml (Backend)"
echo "   - frontend-next/vercel.json (Frontend)"
echo "   - Procfile (Heroku alternative)"
echo "   - DEPLOYMENT.md (Full guide)"
echo ""
echo "📚 See DEPLOYMENT.md for detailed instructions"
