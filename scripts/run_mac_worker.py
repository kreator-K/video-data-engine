"""Process hosted studio jobs on this Mac using local provider configuration."""
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import dotenv_values,load_dotenv
def run():
    load_dotenv(ROOT/'.env')
    cloud=dotenv_values(ROOT/'.env.vercel.local')
    if not cloud.get('POSTGRES_URL'):raise SystemExit('Pull the linked Vercel environment into .env.vercel.local first.')
    os.environ['POSTGRES_URL']=cloud['POSTGRES_URL']
    os.environ.setdefault('MAX_SOURCE_DURATION_SECONDS','1800')
    os.environ.setdefault('MAX_SOURCE_BYTES','314572800')
    from worker import main
    main()

if __name__=='__main__':run()
