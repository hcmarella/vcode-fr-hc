import { useParams } from "react-router-dom";

export default function SessionChatPage() {
  const { id } = useParams();
  return (
    <div>
      <h1 className="text-2xl font-semibold">Session: {id}</h1>
      <p className="mt-2 text-sm text-slate-500">
        Streamed chat + tool-call view lands in Phase 4.
      </p>
    </div>
  );
}
