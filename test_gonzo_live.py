import asyncio
import os
import sys
import subprocess
import platform
import ssl
from datetime import datetime
from dotenv import load_dotenv
from langchain.callbacks.tracers import LangChainTracer
from langsmith import Client