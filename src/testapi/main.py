import warnings
from datetime import datetime
from crew import ReconCrew
import validators
import sys

# Suppress Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the reconnaissance crew with user-provided target URL.
    """
    print("\n=== Reconnaissance Crew ===")
    print("WARNING: Ensure you have permission to scan the target URL. Unauthorized scanning may be illegal.")
    try:
        target_url = input("Enter the target URL for reconnaissance (e.g., https://example.com): ").strip()
        
        # Basic URL validation
        if not target_url:
            raise ValueError("URL cannot be empty")
        if not validators.url(target_url):
            raise ValueError(f"Invalid URL format: {target_url}")

        # Normalize URL (remove protocol for tools that expect domain only)
        domain = target_url.replace("https://", "").replace("http://", "").rstrip("/")
        
        recon_crew = ReconCrew(domain)
        result = recon_crew.create_crew().kickoff()

        # Save results to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"recon_results_{timestamp}.md"

        with open(output_file, "w") as f:
            f.write(f"# Reconnaissance Results for {target_url}\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(str(result))

        print(f"\nResults have been saved to {output_file}")

    except ValueError as ve:
        print(f"Input error: {ve}", file=sys.stderr)
        sys.exit(1)
    except EnvironmentError as ee:
        print(f"Environment error: {ee}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while running the crew: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run()