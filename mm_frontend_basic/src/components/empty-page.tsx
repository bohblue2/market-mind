import { BookmarkIcon } from 'lucide-react'

export function EmptyPage() {
  const messages = [
    "풀리지 않은 정보일수록 더 가치있습니다.",
    "남들이 모르는 정보를 찾아보세요.",
    "덜 읽고 더 잘 매수하세요.",
    "더 많은 정보를 발견해보세요."
  ];
  const randomMessage = messages[Math.floor(Math.random() * messages.length)];

  return (
    <div className="flex flex-1 flex-col items-center justify-center space-y-4">
      <div className="space-y-2 text-center">
        <div className="flex items-center justify-center space-x-1.5">
          <BookmarkIcon size={20} />
          <h1 className="text-xl">에지 - Ai Zzirasi</h1>
        </div>
        <p className="text-sm">{randomMessage}</p>
      </div>
    </div>
  )
}
