import subprocess
import sys
import time
from datetime import datetime

def run_step(script_name):
    """აშვებს სკრიპტს და ელოდება მის დასრულებას"""
    print(f"\n{'='*50}")
    print(f"🚀 პროცესი დაიწყო: {script_name}")
    print(f"⏰ დრო: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}\n")
    
    try:
        # აშვებს სკრიპტს და ბეჭდავს მის გამონატანს რეალურ დროში
        process = subprocess.run([sys.executable, script_name], check=True)
        
        if process.returncode == 0:
            print(f"\n✅ {script_name} წარმატებით დასრულდა!")
            return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ შეცდომა {script_name}-ის მუშაობისას!")
        print(f"შეცდომის კოდი: {e}")
        return False
    except Exception as e:
        print(f"\n⚠️ გაუთვალისწინებელი შეცდომა: {e}")
        return False

def main():
    start_all = time.time()
    
    # 📝 ნაბიჯების თანმიმდევრობა
    steps = [
        "get_links.py",          # აკუსტიკის ლინკების აღება
        "geovoice_get_links.py",  # გეოვოისის ლინკების აღება
        "scraper.py",            # აკუსტიკის სკანირება
        "crawler.py",            # გეოვოისის სკანირება
        "compare_prices.py"      # შედარება და რეპორტი
    ]
    
    for script in steps:
        success = run_step(script)
        if not success:
            print(f"\n🛑 პროცესი შეწყდა {script}-ზე მომხდარი შეცდომის გამო.")
            sys.exit(1)
            
    end_all = time.time()
    total_min = round((end_all - start_all) / 60, 1)
    
    print(f"\n{'⭐'*20}")
    print(f"🎉 მისალოცია! სრული ციკლი დასრულდა.")
    print(f"⏱️ მთლიანი დრო: {total_min} წუთი")
    print(f"📅 თარიღი: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'⭐'*20}")

if __name__ == "__main__":
    main()