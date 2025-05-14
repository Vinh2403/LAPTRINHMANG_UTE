# main.py
import warnings
from datetime import datetime
from crew import ReconCrew # Đảm bảo import đúng
import validators
import sys

# Suppress Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd") # Thêm nếu cần

def run():
    """
    Run the reconnaissance crew with user-provided target URL.
    """
    print("\n=== Reconnaissance Crew ===")
    print("WARNING: Ensure you have permission to scan the target URL. Unauthorized scanning may be illegal.")

    try:
        # Nhập target có thể là domain hoặc URL đầy đủ
        raw_target_input = input("Enter the target domain or URL for reconnaissance (e.g., example.com or https://example.com): ").strip()
        if not raw_target_input:
            raise ValueError("Target cannot be empty")

        # Chuẩn hóa input thành domain (ví dụ: example.com)
        domain = raw_target_input.replace("https://", "").replace("http://", "").split('/')[0].rstrip("/")
        
        # Kiểm tra lại domain sau khi chuẩn hóa có hợp lệ không (ví dụ không phải là IP)
        # Validators.domain() có thể hữu ích ở đây, nhưng đơn giản là check không rỗng là được
        if not domain:
             raise ValueError(f"Could not extract a valid domain from: {raw_target_input}")
        print(f"Normalized target domain: {domain}")


        recon_crew_instance = ReconCrew(domain) # Truyền domain đã chuẩn hóa
        crew = recon_crew_instance.create_crew()
        print("\nKicking off the Reconnaissance Crew...")
        result = crew.kickoff()

        # Save results to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"recon_results_{domain.replace('.', '_')}_{timestamp}.md" # Thêm domain vào tên file

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Reconnaissance Report for {raw_target_input} (Target Domain: {domain})\n\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Crew Execution Log & Raw Tool Outputs (Aggregated)\n\n")
            # Nếu result là một dictionary (với verbose=2, result có thể chứa nhiều thông tin hơn)
            # Hoặc nếu bạn muốn lấy output của từng task, bạn có thể truy cập crew.tasks[index].output
            # Tuy nhiên, với agent tổng hợp, output của task cuối cùng (reporting_task) sẽ là cái chúng ta muốn.
            # Result của kickoff() là output của task cuối cùng nếu process là sequential.
            f.write(str(result)) 

        print(f"\nReconnaissance complete. Results have been saved to {output_file}")
        print("\n--- Final Report ---")
        print(result) # In ra output của agent tổng hợp

    except ValueError as ve:
        print(f"Input error: {ve}", file=sys.stderr)
        sys.exit(1)
    except EnvironmentError as ee:
        print(f"Environment error: {ee}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while running the crew: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc() # In ra traceback để debug dễ hơn
        sys.exit(1)

if __name__ == "__main__":
    run()