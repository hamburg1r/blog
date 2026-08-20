---
published: true
title: "Fake Bank, Part 2: Idempotency, Ledgers, and Naming Things Against My Will"
cover_image: "https://raw.githubusercontent.com/hamburg1r/blog/refs/heads/main/blogs/fake-bank/post-02/Cover.png"
description: "Part 2 of building a fake bank in public — payment reversals, idempotency (and why it's overrated), journal entries, and a ledger endpoint naming battle I lost."
tags: java, spring, backend, learning
series: Fake Bank, Real Problems
canonical_url:
---

Welcome back, it has been ~2.5 months since my last post. What can I say, consistency is my middle name.

Jokes apart i've been busy, just not on this project :'). Still, there has been some progress.

## Working
A rough diagram I mocked up real quick:
![Sequence Diagram](https://raw.githubusercontent.com/hamburg1r/blog/refs/heads/main/blogs/fake-bank/post-02/SequenceDiagram.png)


## Folder structure
So, currently I have started with a very basic DDD style structure:

```text
ledgerflow/
├── docs/
├── src/main/java/io/ledgerflow/
│   ├── account/
│   ├── ledger/
│   ├── paymentTransaction/
│   └── user/                 ← each module below
├── flake.nix
└── pom.xml
```

<details>
<summary>Full package layout</summary>

```text
src/main/java/io/ledgerflow/
├── LedgerflowApplication.java
├── account/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── error/
│   └── infra/
├── ledger/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── error/
│   └── infra/
├── paymentTransaction/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── error/
│   └── infra/
└── user/
    ├── api/
    ├── application/
    ├── domain/
    ├── error/
    └── infra/
```

</details>

I have segregated every service into its own module and every module has its own set of packages: api, application, domain, error and infra. As you can already see above.

api - handles how to communicate with the world outside
application - business logic goes here
domain - entities and rules enforced on them
error - custom errors
infra - made for communication with other infrastructure like database

## New Schema
I have also slightly tweaked the er diagram too.
![New Schema](https://raw.githubusercontent.com/hamburg1r/blog/refs/heads/main/blogs/fake-bank/post-02/Schema.png)

So, what's changed you ask? Renamed ledger.type to be ledger.direction, it feels more natural now. And We have started with.. \*\*_drumroll noises_\*\* IDEMPOTENCY!!!
The keys have been added to PaymentTransactions table. And guess what, there's a new PaymentTransactionReversal table too.

## Why another table for handling Payment Transaction Reversal?
For a while I was considering using a simple flag to mark reversal, maybe update the original transaction itself. But I dropped that idea, I mean it will cause us to lose some about transactions, like when was the reversal initiated? no one knows.

So, the next logical step? create another transaction row with its own states, and a separate table for associating both transaction, the original and the reversal. All in all improved audit experience.

Btw, I hope you read my [previous post](https://dev.to/hamburgir/lets-build-a-fake-bank-to-learn-backend-engineering-4epa) there I mentioned about the "Act as a socratic teacher" prompt addition. I kid you not did it make me question my decisions. Holy shit, even I was questioning my own choices. 10/10 would recommend 100%.
"What makes you question yourself makes you grow" ~Sun Tzu, maybe idk

Also, there's an additional benefit of having a separate table, we can later have partial refunds too. But I don't think I'll be doing that really. I mean if we reach at the point of adding useless features we are just wasting time. Might change my mind later though.

## Idempotency
Honestly, after reading about idempotency i am very underwhelmed. Idempotency is the mist noble (sekiro reference) of programming field, imho. The word sounds so complicated but in reality we are just checking if key exists and return the item associated or create a new one if it doesn't. That's it. That was the whole concept of idempotency. I won't lie its a great concept but I was expecting more.

Okay rant is over. So, what I decided to do is have idempotency keys in transaction tables as they will be public facing and need to be resilient to users' retries.

Firstly, as you would expect PaymentTransaction table has idempotency, but why does PaymentTransactionReversal need one? The reason is simple. For this project I have decided to keep operations inside their own sandboxes. So, when we need to check if a reversal has already happend or not we first query the PaymentTransactionReversalRepository, if it exists we then fetch the reversal transaction from PaymentTransaction table and return to the user.

## Ledger related problems
Problem: Multiple ledger in single transaction. How will you handle that?
Solution: Journal.

Journal rabbit hole can also go deep but I have decided to not follow it. Just use it for validation of entries. All the entries in the journal should sum up to 0 that's it. Hope you didn't forget the formula for double entry ;)

A part of my current setup I don't really like but it had to be that way:
I had to make `/ledger/accounts/{accountId}/balance` for `getBalance` and `/ledger/transactions/{transactionId}` for `getEntry`. I like controllers sharing single root `/ledger` then adding at most 2 parts for eg `/transaction/{transactionId}/reverse`. I had to go against my will, although this setup works better.


## Random things
A temporary auth like setup is implemented which just checks if reversal initiator and original transaction initiator are same or not

I have been pondering about adding gRPC. Really cool protocol. Maybe I won't even touch REST. We will talk about it in the next post.

---

Next up: Working on tests, I mean they'll be generated by AI but we have to vet it still, can't trust AI blindly. Also might be working on transition towards microservices. Till now I have taken good care to make it decoupled as much as possible but currently transaction service relies on ledger service being available locally.
