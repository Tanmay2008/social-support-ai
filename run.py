#!/usr/bin/env python3
"""
Social Support AI - Main Entry Point

This script provides a command-line interface to run different components of the
Social Support AI system, including the API server, data processing, and demo mode.
"""

import os
import sys
import argparse
import logging
import uvicorn
from typing import Optional, List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('social_support_ai.log')
    ]
)
logger = logging.getLogger(__name__)

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.absolute())
sys.path.insert(0, PROJECT_ROOT)


class SocialSupportAI:
    """Main class for the Social Support AI system."""
    
    def __init__(self):
        self.initialized = False
        self.workflow = None
        self.db_manager = None
        
    def initialize(self):
        """Initialize the system components."""
        if self.initialized:
            return
            
        logger.info("Initializing Social Support AI system...")
        
        try:
            # Import required modules
            from data_pipeline.database_manager import DatabaseManager
            from agent_orchestration.workflow_orchestrator import get_workflow
            
            # Initialize database
            logger.info("Initializing database...")
            self.db_manager = DatabaseManager()
            self.db_manager.initialize_database()
            
            # Initialize workflow orchestrator
            logger.info("Initializing workflow orchestrator...")
            self.workflow = get_workflow()
            
            self.initialized = True
            logger.info("System initialization completed successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {str(e)}")
            raise
    
    def run_api_server(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Run the FastAPI server.
        
        Args:
            host: Host to bind the server to
            port: Port to run the server on
            reload: Enable auto-reload for development
        """
        self.initialize()
        logger.info(f"Starting API server on {host}:{port}")
        
        uvicorn.run(
            "api_server.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            workers=4 if not reload else 1
        )
    
    def run_frontend(self, port: int = 8501):
        """Run the Streamlit frontend.
        
        Args:
            port: Port to run the frontend on
        """
        self.initialize()
        logger.info(f"Starting Streamlit frontend on port {port}")
        
        # Set environment variables for Streamlit
        os.environ["STREAMLIT_SERVER_PORT"] = str(port)
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
        
        # Import and run Streamlit
        from streamlit.web import cli as st_cli
        sys.argv = ["streamlit", "run", "frontend/streamlit_app.py", "--server.port", str(port)]
        sys.exit(st_cli.main())
    
    def process_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single social support application.
        
        Args:
            application_data: Dictionary containing application data
            
        Returns:
            Dictionary containing processing results
        """
        self.initialize()
        logger.info("Processing application...")
        
        try:
            # Process the application through the workflow
            result = self.workflow.process_application(application_data)
            logger.info("Application processed successfully.")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process application: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_demo(self, num_applications: int = 5):
        """Run a demo with sample applications.
        
        Args:
            num_applications: Number of sample applications to process
        """
        self.initialize()
        logger.info(f"Running demo with {num_applications} sample applications...")
        
        try:
            from data_pipeline.synthetic_data_generator import SyntheticDataGenerator
            
            # Generate synthetic data
            generator = SyntheticDataGenerator()
            sample_data = generator.generate_sample_applications(num_applications)
            
            # Process each application
            results = []
            for i, app_data in enumerate(sample_data):
                logger.info(f"Processing application {i+1}/{num_applications}")
                result = self.process_application(app_data)
                results.append({
                    "application_id": f"DEMO-{i:03d}",
                    "status": "success" if result.get("success", False) else "failed",
                    "eligibility_score": result.get("eligibility_score", 0.0),
                    "decision": result.get("decision", {})
                })
            
            # Print summary
            print("\n=== Demo Results ===")
            for result in results:
                print(f"\nApplication: {result['application_id']}")
                print(f"Status: {result['status']}")
                print(f"Eligibility Score: {result['eligibility_score']:.2f}")
                print(f"Decision: {result['decision'].get('status', 'unknown')}")
            
            return results
            
        except Exception as e:
            logger.error(f"Demo failed: {str(e)}")
            return {"success": False, "error": str(e)}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Social Support AI System")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # API Server command
    api_parser = subparsers.add_parser("api", help="Run the API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Frontend command
    frontend_parser = subparsers.add_parser("frontend", help="Run the Streamlit frontend")
    frontend_parser.add_argument("--port", type=int, default=8501, help="Port to run on")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process a single application")
    process_parser.add_argument("input_file", help="Path to JSON file with application data")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run a demo with sample applications")
    demo_parser.add_argument("-n", "--num-applications", type=int, default=5, 
                           help="Number of sample applications to process")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check system status")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    app = SocialSupportAI()
    
    try:
        if args.command == "api":
            app.run_api_server(host=args.host, port=args.port, reload=args.reload)
            
        elif args.command == "frontend":
            app.run_frontend(port=args.port)
            
        elif args.command == "process":
            import json
            with open(args.input_file) as f:
                data = json.load(f)
            result = app.process_application(data)
            print(json.dumps(result, indent=2))
            
        elif args.command == "demo":
            app.run_demo(num_applications=args.num_applications)
            
        elif args.command == "check":
            print("Checking system status...")
            try:
                app.initialize()
                print("✅ System is ready!")
            except Exception as e:
                print(f"❌ System check failed: {str(e)}")
                sys.exit(1)
                
        else:
            print("Please specify a command. Use --help for usage information.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()