import os
import redis.asyncio as redis
import requests
from fastapi import Depends, FastAPI
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

load_dotenv()

GITHUB_API=os.getenv('GITHUB_API')
REDIS_URI=os.getenv('REDIS_URI')

app = FastAPI()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=os.getenv("GEMINI_API_KEY"))

class Response:
    def __init__(self, statusCode=200, data=None, message="Success", success=None):
        self.statusCode = statusCode
        self.data = data
        self.message = message
        if(success != None):
            self.success = success
        else:
            self.success = self.statusCode < 400

class Error(Exception):

    def __init__(self, Response: Response):
        super()
        self.__Response = Response

    def get(self):
        return self.__Response

class GitApi:
    def __init__(self):
        self.default_headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_API}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_commit_diff_list(self, username, repo, since, until, max_commits):
        url = f"https://api.github.com/repos/{username}/{repo}/commits?per_page=20&since={since}&until={until}"
        response = requests.get(url, headers=self.default_headers)
        commits = response.json()

        if response.status_code >= 400:
            raise Error(Response(int(response.status_code), None, "Something went wrong!"))
        
        if len(commits) <= 1:
            raise Error(Response(400, None, "Commits must be greater than one"))
        
        diff_sha = []
        
        for index, commit in enumerate(commits[:max_commits]):
            sha = commit['sha']
            if(index != len(commits)-1):
                diff_sha.append([ sha, commits[index+1]['sha']])

        return diff_sha


    def list_commits(self, username, repo, since=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat(), until=datetime.now(timezone.utc).isoformat(), char_length=280, max_files_each_diff=10, max_commits=10):
        
        diff_sha = self.get_commit_diff_list(username, repo, since, until, max_commits)

        tweet_refrence = ""

        for diff in diff_sha:
            diff_url = f" https://api.github.com/repos/{username}/{repo}/compare/{diff[1]}...{diff[0]}"
            response = requests.get(diff_url, headers={**self.default_headers})

            if response.status_code > 200:
                return Response(int(response.status_code), None, "Error while comparing commits")
            
            data = response.json()

            content = ""

            for idx, file in enumerate(data['files'][:max_files_each_diff]):
                if "patch" in file:
                    content += f"id: {idx},filename: {file['filename']} & changed content: {file['patch']}\n"

            llmResult = llm.invoke([
                ("system", """Your job is to generate one insightful, punchy, and informative lines per change. Avoid summarizing the entire commit; instead, focus on *per-file* or *per-chunk* changes and highlight what was done and why it might matter. These lines should be written as if you're preparing them for a changelog, tweet thread, or AI digest.

                Instructions:
                - Be clear, concise, and slightly casual — it should read well in a tweet.
                - Use technical phrasing but avoid overly verbose descriptions.
                - Each line should ideally be standalone and reusable.
                - Mention what was added, fixed, refactored, or updated.
                - If possible, infer intent (e.g., "Added null check", "Simplified loop logic", "Updated API call to v2").
                - Do not write markdown or code unless it adds meaning.
                - Keep message under 500 characters. """),
                ("human", content)
            ])

            print("llm result: ", llmResult.content)

            tweet_refrence += llmResult.content

        tweet = llm.invoke([("system", f"""You are a developer who tweets about your daily work in a natural, human tone. Should be more natural like human, You will be given a list of code changes or technical improvements from your recent work session.

        Your task is to write a short tweet (under {char_length} characters) that captures what you *did*, *built*, or *learned* today — like you're talking to other devs or followers on Twitter/X. Very precise with a coder perspective

        Focus on:
        - What you implemented or refactored
        - What you learned or realized
        - What felt good, painful, or satisfying
        - A little bit of personality or reflection

        Tone:
        - Friendly, casual, and authentic
        - Not robotic or changelog-style
        - Optional emojis or expressions are great
        - No file names or commit-style messages

        Goal:
        Make it sound like a real dev tweet you'd post to share progress or insights — something real people would want to read or reply to.

        Examples:
        - "Implemented message queues for sending emails in my project and absolutely loved it! 🔥 Message queues finally make sense."
        - "Today I built the forgot password flow with email tokens + expiry logic. Also cleaned up a ton of error handling. Backend is so much cleaner now 🙌"
        - "Swapped out a bunch of custom error stuff for a more structured `ApiError` class. Feels way more robust. Next up: logging 👀"
        - "Just finished a user registration overhaul! 🔐 Email verification with queueing, token hashing, and stricter env variable validation. Plus, better logging all around. Feels good to ship secure code! 💪 #typescript #security #backend"

        Now, write a tweet based on the work described below.
        """), ("human", tweet_refrence)])

        print("tweet", tweet.content)

        return Response(200, { 
            "tweet": tweet.content
         }, "Your today's tweet message is here.")


api = GitApi()

app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:9000'], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    redis_connection = redis.from_url(REDIS_URI, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)

@app.get('/{username}/{repository}', dependencies=[Depends(RateLimiter(times=20, seconds=60*60))])
async def healthCheck(username, repository, char_length=280, max_file_each_diff=10, max_commits=10):
    try:
        result = api.list_commits(username, repository, char_length=char_length, max_files_each_diff=max_file_each_diff, max_commits=max_commits)
    except Error as e:
        return e.get()
    if result:
        return result
    return Response(200, None)

