---------------------------- MODULE QueueConsumer ----------------------------
(***************************************************************************)
(* TEMPLATE: at-least-once queue consumer that writes to a shared store.   *)
(* Copy to docs/model/, rename, and replace every assumption below with    *)
(* what the code actually does. Cite ledger IDs next to each action.       *)
(*                                                                         *)
(* This is a MODEL of the design, not the code. A pass means "no violation *)
(* within these bounds and assumptions". A violation is a candidate defect *)
(* until each step of the trace is confirmed in the code.                  *)
(***************************************************************************)
EXTENDS Naturals

CONSTANTS
    Msgs,         \* finite set of message ids (use 2 or 3)
    Workers,      \* finite set of worker ids (use 2)
    MaxCrashes,   \* bound on worker crashes / visibility-timeout redeliveries
    Idempotent,   \* TRUE if the consumer dedupes before writing (ASSUMPTION A1)
    NONE          \* model value meaning "no message" (set NONE = NONE in the .cfg)

ASSUME NONE \notin Msgs

VARIABLES
    queue,        \* messages available for delivery
    held,         \* held[w] = message w is processing, or NONE
    wrote,        \* wrote[w] = TRUE once w has done its write for held[w]
    acked,        \* messages removed from the queue for good
    applied,      \* applied[m] = number of times m's effect hit the store
    seen,         \* idempotency keys recorded in the store
    crashes       \* number of crashes so far

vars == <<queue, held, wrote, acked, applied, seen, crashes>>

TypeOK ==
    /\ queue \subseteq Msgs
    /\ acked \subseteq Msgs
    /\ seen  \subseteq Msgs
    /\ \A w \in Workers : held[w] \in Msgs \union {NONE}
    /\ \A w \in Workers : wrote[w] \in BOOLEAN
    /\ \A m \in Msgs : applied[m] \in Nat
    /\ crashes \in 0..MaxCrashes

Init ==
    /\ queue   = Msgs
    /\ held    = [w \in Workers |-> NONE]
    /\ wrote   = [w \in Workers |-> FALSE]
    /\ acked   = {}
    /\ applied = [m \in Msgs |-> 0]
    /\ seen    = {}
    /\ crashes = 0

\* Source: consumer receive loop (cite ledger ID / file:line)
Receive(w) ==
    /\ held[w] = NONE
    /\ \E m \in queue :
         /\ held'  = [held EXCEPT ![w] = m]
         /\ queue' = queue \ {m}
    /\ UNCHANGED <<wrote, acked, applied, seen, crashes>>

\* Source: handler write (cite ledger ID / file:line)
\* ASSUMPTION A1: when Idempotent, the key check and the business write
\* commit in ONE transaction. Confirm in code before trusting a pass.
Write(w) ==
    /\ held[w] /= NONE
    /\ ~wrote[w]
    /\ wrote' = [wrote EXCEPT ![w] = TRUE]
    /\ UNCHANGED <<queue, held, acked, crashes>>
    /\ LET m == held[w] IN
         IF Idempotent /\ m \in seen
            THEN UNCHANGED <<applied, seen>>
            ELSE /\ applied' = [applied EXCEPT ![m] = @ + 1]
                 /\ seen'    = seen \union {m}

\* Source: ack call (cite ledger ID / file:line)
Ack(w) ==
    /\ held[w] /= NONE
    /\ wrote[w]
    /\ acked' = acked \union {held[w]}
    /\ held'  = [held EXCEPT ![w] = NONE]
    /\ wrote' = [wrote EXCEPT ![w] = FALSE]
    /\ UNCHANGED <<queue, applied, seen, crashes>>

\* ASSUMPTION A2: a crash (or visibility timeout) can happen at ANY point,
\* including after the write and before the ack. The message is redelivered.
Crash(w) ==
    /\ held[w] /= NONE
    /\ crashes < MaxCrashes
    /\ queue'   = queue \union {held[w]}
    /\ held'    = [held EXCEPT ![w] = NONE]
    /\ wrote'   = [wrote EXCEPT ![w] = FALSE]
    /\ crashes' = crashes + 1
    /\ UNCHANGED <<acked, applied, seen>>

\* Terminal state: lets TLC tell "finished" from a real deadlock.
Done == acked = Msgs /\ UNCHANGED vars

Next == (\E w \in Workers : Receive(w) \/ Write(w) \/ Ack(w) \/ Crash(w)) \/ Done

Spec == Init /\ [][Next]_vars

----------------------------------------------------------------------------
\* PROPERTIES

\* Each message's effect reaches the store at most once.
AtMostOnce == \A m \in Msgs : applied[m] <= 1

\* No message disappears: it is queued, held, or acked.
NoLostMessage ==
    \A m \in Msgs : m \in queue \/ m \in acked \/ \E w \in Workers : held[w] = m
=============================================================================
