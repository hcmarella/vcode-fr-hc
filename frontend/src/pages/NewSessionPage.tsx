import EmptyState from "../components/ui/EmptyState";
import PageHeader from "../components/ui/PageHeader";

export default function NewSessionPage() {
  return (
    <div>
      <PageHeader title="Start a session" subtitle="Persona picker + git repo URL form." />
      <EmptyState message="Not built yet -- see /sessions for why this is a separate, larger effort." />
    </div>
  );
}
