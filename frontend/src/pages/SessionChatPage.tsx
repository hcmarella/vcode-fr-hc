import { useParams } from "react-router-dom";

import EmptyState from "../components/ui/EmptyState";
import PageHeader from "../components/ui/PageHeader";

export default function SessionChatPage() {
  const { id } = useParams();
  return (
    <div>
      <PageHeader title={`Session ${id}`} subtitle="Streamed chat + tool-call view." />
      <EmptyState message="Not built yet -- see /sessions for why this is a separate, larger effort." />
    </div>
  );
}
