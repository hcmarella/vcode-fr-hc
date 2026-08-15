# Production sync queue -- what SYNC_QUEUE_BACKEND=sqs points the backend and
# worker at (see backend/app/sync_engine/queue.py). Replaces the Postgres
# SELECT...FOR UPDATE SKIP LOCKED polling used locally: at real multi-team
# push volume, a managed queue means the worker fleet isn't hammering
# Postgres with polling queries just to find out there's no work, and you get
# retry-via-visibility-timeout for free instead of hand-rolling it.
resource "aws_sqs_queue" "sync_queue_dlq" {
  name                      = "${var.project_name}-${var.environment}-sync-dlq"
  message_retention_seconds = 1209600 # 14 days -- long enough to investigate a stuck job before it's gone
}

resource "aws_sqs_queue" "sync_queue" {
  name = "${var.project_name}-${var.environment}-sync"

  # Must exceed the slowest realistic sync (git clone + parse + upsert of a
  # large vcode-w-hc). If a sync legitimately takes longer than this, SQS
  # will redeliver it to a second worker while the first is still running --
  # widen this before that becomes a real double-processing risk, not after.
  visibility_timeout_seconds = 300

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.sync_queue_dlq.arn
    maxReceiveCount     = 5 # after 5 failed attempts, stop retrying and let a human look at the DLQ
  })
}
