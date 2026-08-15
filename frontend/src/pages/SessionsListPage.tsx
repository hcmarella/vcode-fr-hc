import EmptyState from "../components/ui/EmptyState";
import PageHeader from "../components/ui/PageHeader";

export default function SessionsListPage() {
  return (
    <div>
      <PageHeader title="Your sessions" subtitle="Sandboxed, per-repo persona chat sessions." />
      <EmptyState message="Not built yet -- this needs a real sandbox_engine (container-per-session code execution), a distinct and larger effort from the rest of this portal." />
    </div>
  );
}
