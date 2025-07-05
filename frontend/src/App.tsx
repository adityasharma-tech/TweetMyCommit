import { ArrowRightIcon, StarIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCallback, useId, useState } from 'react';
import { Input } from '@/components/ui/input';
import { LoaderCircleIcon } from 'lucide-react';
import axios from 'axios';

export default function App() {
  const inputId = useId();

  const [loading, setLoading] = useState(false);

  const [input, setInput] = useState('');

  const handleSubmit = useCallback(()=> {
    setLoading(true);

    try {
      axios.post(`${import.meta.env.BASE_URL}`)
    } catch (error) {
      
    } finally {
      setLoading(false);
    }
  }, [])

  return (
    <main className="w-screen h-screen dark:bg-neutral-950 flex flex-col items-center">
      <header className="flex justify-between items-center py-4 px-10 w-full">
        <div>
          <span className="font-medium text-lg">TweetMyCommit</span>
        </div>
        <div>
          <Button>
            <StarIcon
              className="-ms-1 opacity-60"
              size={16}
              aria-hidden="true"
            />
            <span className="flex items-baseline gap-2">
              Star
              <span className="text-primary-foreground/60 text-xs">1</span>
            </span>
          </Button>
        </div>
      </header>
      <div className="max-w-6xl h-full w-full flex items-center flex-col justify-center gap-y-10">
        <div className="text-center">
          <h1 className="text-4xl max-w-4xl" style={{ textWrap: 'balance' }}>
            Auto-tweet today's commits—Code. Commit. Tweet.
          </h1>
          <h2 className="text-sm [text-wrap:balance] my-5 text-neutral-400">
            TweetMYComit lets you auto-tweet your GitHub commits from today.
            Share your daily progress with the world—no copy-paste needed.
          </h2>
        </div>
        <form onSubmit={handleSubmit} className="flex gap-x-3">
          <div className="*:not-first:mt-2">
            <div className="relative">
              <Input
                value={input}
                onChange={(e)=>setInput(e.target.value)}
                id={inputId}
                className="peer ps-38"
                placeholder="adityasharma-tech"
                type="text"
              />
              <span className="text-muted-foreground pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3 text-sm peer-disabled:opacity-50">
                https://github.com/
              </span>
            </div>
          </div>
          <Button type="submit" disabled={loading}>
            {loading && <LoaderCircleIcon
              className="-ms-1 animate-spin"
              size={16}
              aria-hidden="true"
            />}
            Continue
            {!loading && <ArrowRightIcon
              className="-me-1 opacity-60 transition-transform group-hover:translate-x-0.5"
              size={16}
              aria-hidden="true"
            />}
          </Button>
        </form>

        <div className='ring ring-neutral-600 rounded-lg p-2 px-3 py-5 bg-neutral-900'>
          <p className='max-w-xl text-sm text-neutral-300 text-center'>
            🚀 Today's Commits 🛠️ Refactored user auth logic 📦 Added cache
            layer to API ✅ Fixed broken tests in auth.spec.js 🔧 Updated README
            with setup steps #BuildInPublic #100DaysOfCode #devlog
          </p>
        </div>
      </div>
    </main>
  );
}
