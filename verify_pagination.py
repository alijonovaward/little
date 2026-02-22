import requests
import json

def verify():
    url = "https://million-halal-mart-6jij.onrender.com/api/product/goods/"
    print(f"Fetching Page 1: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        count = data.get('count')
        next_page = data.get('next')
        results = data.get('results', [])
        
        print(f"Page 1 - Count: {count}")
        print(f"Page 1 - Next: {next_page}")
        print(f"Page 1 - Results Length: {len(results)}")
        
        if next_page:
            print(f"\nFetching Page 2: {next_page}")
            response2 = requests.get(next_page, timeout=30)
            response2.raise_for_status()
            data2 = response2.json()
            
            results2 = data2.get('results', [])
            print(f"Page 2 - Results Length: {len(results2)}")
            print(f"Page 2 - Previous: {data2.get('previous')}")
            
            if count == 25 and len(results) == 20 and len(results2) == 5:
                print("\n✅ PAGINATION IS WORKING PERFECTLY!")
            else:
                print("\n❌ PAGINATION DATA MISMATCH!")
        else:
            print("\n❌ NEXT PAGE LINK MISSING!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
