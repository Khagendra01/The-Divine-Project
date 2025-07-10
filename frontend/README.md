# Egent Frontend

A modern Next.js frontend for the Egent AI Task Manager backend.

## Features

- 🎯 Create and manage AI-powered tasks
- 📊 Real-time task progress tracking
- 🔍 Detailed task status and subtask monitoring
- 🎨 Modern, responsive UI with Tailwind CSS
- ⚡ Fast development with Next.js 14 and TypeScript

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Egent backend running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env.local` file in the frontend directory:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

### Quick Start
1. Click "Create Demo User" to set up a test user
2. Click "Create Demo Task" to create a sample AI task
3. Or create your own task by describing what you want the AI to help with

### Creating Tasks
- Enter a detailed description of what you want the AI to accomplish
- The system will break down your request into subtasks
- Monitor progress in real-time
- View detailed status and agent executions

### Task Management
- View all your tasks in the dashboard
- Click "View Details" to see progress, subtasks, and agent executions
- Real-time updates show current status and progress

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Main page component
├── components/            # Reusable UI components
│   └── ui/               # Base UI components
├── lib/                   # Utilities and types
│   ├── api.ts            # API client
│   ├── types.ts          # TypeScript interfaces
│   └── utils.ts          # Utility functions
└── package.json          # Dependencies and scripts
```

## API Integration

The frontend communicates with the Egent backend API:

- **Health Check**: `/health`
- **Users**: `/users`, `/users/{id}`, `/users/{id}/preferences`
- **Tasks**: `/tasks`, `/tasks/{id}`, `/tasks/{id}/progress`
- **Demo**: `/demo/create-user`, `/demo/task`, `/demo/tasks/{id}`

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **UI Components**: Custom components with shadcn/ui patterns

## Configuration

### Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

### API Configuration

The frontend expects the backend to be running on the configured API URL. Make sure your Egent backend is running and accessible.

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure the backend is running on the correct port
   - Check the `NEXT_PUBLIC_API_URL` environment variable
   - Verify CORS is enabled on the backend

2. **TypeScript Errors**
   - Run `npm install` to ensure all dependencies are installed
   - Check that all type definitions are properly imported

3. **Build Errors**
   - Clear the `.next` directory: `rm -rf .next`
   - Reinstall dependencies: `rm -rf node_modules && npm install`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Egent AI Task Manager system. 