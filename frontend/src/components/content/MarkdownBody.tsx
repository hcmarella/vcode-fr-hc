import ReactMarkdown from "react-markdown";

export default function MarkdownBody({ children }: { children: string }) {
  return (
    <div className="prose prose-slate mt-4 max-w-none prose-headings:font-semibold prose-pre:bg-slate-900 prose-pre:text-slate-100">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  );
}
