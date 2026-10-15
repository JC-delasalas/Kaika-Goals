#!/usr/bin/env python3
"""Start the private, loopback-only Kaika FastAPI application."""
from pathlib import Path
import argparse,uvicorn
from api import create_app
if __name__=='__main__':
 parser=argparse.ArgumentParser()
 parser.add_argument('--port',type=int,default=8787)
 parser.add_argument('--fixtures',action='store_true')
 parser.add_argument('--connected-workshop',action='store_true')
 args=parser.parse_args()
 uvicorn.run(create_app(Path(__file__).resolve().parent,args.port,args.fixtures),host='127.0.0.1',port=args.port,access_log=False)
