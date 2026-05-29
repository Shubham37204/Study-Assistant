import { useRef, useState } from 'react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { useUpload } from '@/hooks/useUpload'

const ALLOWED = ['.pdf', '.txt', '.md', '.png', '.jpg', '.jpeg', '.webp']
const MAX_MB = 50

function UploadZone() {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)
  const { mutate: upload, isPending } = useUpload()

  function validate(file) {
    const ext = '.' + file.name.split('.').pop().toLowerCase()

    if (!ALLOWED.includes(ext)) {
      toast.error(`${ext} files aren't supported`)
      return false
    }

    if (file.size > MAX_MB * 1024 * 1024) {
      toast.error(`File must be under ${MAX_MB}MB`)
      return false
    }

    return true
  }

  function handleFile(file) {
    if (!file) return
    if (!validate(file)) return
    upload(file)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  function handleChange(e) {
    handleFile(e.target.files[0])
    e.target.value = ''
  }

  return (
    <div
      onClick={() => !isPending && inputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      className={cn(
        'flex h-24 cursor-pointer flex-col items-center justify-center rounded-lg',
        'border-2 border-dashed transition-colors',
        dragging
          ? 'border-slate-400 bg-slate-50'
          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50',
        isPending && 'cursor-not-allowed opacity-50'
      )}
    >
      {isPending ? (
        <p className="text-xs text-slate-400">Processing...</p>
      ) : (
        <>
          <p className="text-xs font-medium text-slate-500">
            {dragging ? 'Drop to upload' : 'Click or drag a file'}
          </p>
          <p className="mt-1 text-xs text-slate-300">
            PDF · TXT · MD · PNG · JPG
          </p>
        </>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={ALLOWED.join(',')}
        onChange={handleChange}
        disabled={isPending}
        className="hidden"
      />
    </div>
  )
}

export default UploadZone
