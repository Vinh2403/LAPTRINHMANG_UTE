# main.py
import warnings
from datetime import datetime
from crew import ReconCrew
import validators
import sys
import json

# Suppress Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the reconnaissance crew with user-provided target URL and optional tool parameters.
    """
    print("\n=== Reconnaissance Crew ===")
    print("WARNING: Ensure you have permission to scan the target URL. Unauthorized scanning may be illegal.")

    try:
        # Input target domain or URL
        raw_target_input = input("Enter the target domain or URL for reconnaissance (e.g., example.com or https://example.com): ").strip()
        if not raw_target_input:
            raise ValueError("Target cannot be empty")

        # Normalize input to domain (e.g., example.com)
        domain = raw_target_input.replace("https://", "").replace("http://", "").split('/')[0].rstrip("/")
        if not domain:
            raise ValueError(f"Could not extract a valid domain from: {raw_target_input}")
        print(f"Normalized target domain: {domain}")

        # Optional: Allow user to specify custom tool parameters
        custom_params_input = input("Enter custom tool parameters as JSON (e.g., {\"dirsearch_threads\": \"5\"}) or press Enter to use defaults: ").strip()
        custom_params = json.loads(custom_params_input) if custom_params_input else {}

        recon_crew_instance = ReconCrew(domain)
        crew = recon_crew_instance.create_crew()
        print("\nKicking off the Reconnaissance Crew...")
        result = crew.kickoff()

        # Save results to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_domain = domain.replace('.', '_')
        output_file = f"recon_results_{safe_domain}_{timestamp}.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Reconnaissance Report for {raw_target_input} (Target Domain: {domain})\n\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Crew Execution Log & Raw Tool Outputs (Aggregated)\n\n")
            f.write(str(result))

        print(f"\nReconnaissance complete. Results have been saved to {output_file}")
        print("\n--- Final Report ---")
        print(result)

    except ValueError as ve:
        print(f"Input error: {ve}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Invalid JSON format for custom parameters", file=sys.stderr)
        sys.exit(1)
    except EnvironmentError as ee:
        print(f"Environment error: {ee}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while running the crew: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run()