# Clash Royale Simulator + RL Agent: Project Plan

A step-by-step plan for building a project like Hasty-CR (deterministic simulator, RL agent, optional live-play bridge) around **your own deck** instead of 2.6 Hog Cycle.

**How to use this file:** work top to bottom. Each phase has a goal, tasks (checkboxes), and a "done when" check. Don't start the next phase until the current one's check passes. Most of the pain in this kind of project comes from skipping a verification step and discovering the problem three phases later.

---

## Phase 0: Decide scope and pick your deck (Day 1)

**Goal:** a clear, bounded target so the project doesn't balloon.

- [x] Pick your deck (8 cards). Write it down in `docs/DECK.md`.
- [x] List the deck's **mechanics that are hard to simulate**. This decides your difficulty:
  - *Easy:* simple troops, direct-damage spells (Fireball, Zap, Log), cycle decks.
  - *Medium:* buildings (Cannon, Tesla), splash damage, targeting priorities, spawners.
  - *Hard:* charging units (Prince, Ram, Battle Ram), death effects chains (Golem, Lava Hound), channeled/evolving cards, Mirror/Clone/Rage-style effects, heavy swarm physics.
- [x] Decide your **success definition** up front, e.g. "beats my rule-engine baseline 80%+ and beats 3 meta decks 70%+ on held-out seeds."
- [x] Decide whether live play is in scope (see Phase 12 caveats). Default: **no**.
- [x] Choose a stack: Python 3.12, NumPy, PyTorch, pytest. Optional: Numba/Cython later if the sim is too slow.

**Tip:** if this is your first time, pick a deck with few hard mechanics. A cheap cycle deck or a simple beatdown deck will get you to a working agent far faster than a deck built on charging units or Golem death chains.

**Done when:** `docs/DECK.md` lists the 8 cards, the mechanics risk list, and the success definition.

---

## Phase 1: Repo skeleton (Day 1-2)

**Goal:** a clean project you can run tests in from minute one.

- [ ] Create the repo with this layout:

```
my-cr/
├── pyproject.toml
├── README.md
├── LICENSE
├── data/            # card/tower/arena data
├── docs/            # decision logs, deck notes, limitations
├── sim/             # engine, env, training
├── scripts/         # evaluation, probes, supervisor
├── tools/           # calibration, data extraction
├── tests/           # one file per behavior
└── runs/            # checkpoints, logs (gitignored)
```

- [ ] `pyproject.toml` with extras: `[dev]` (pytest, torch, numpy), later `[live]`.
- [ ] `pip install -e ".[dev]"` works and `pytest` runs (even with zero tests).
- [ ] Set up a `docs/DECISIONS.md` log. Every time you make a judgement call (a number you guessed, a mechanic you simplified), write it down. Hasty-CR's honesty about its own approximations is a big part of why it's credible.

**Done when:** fresh clone → install → `pytest` passes in one command.

---

## Phase 2: Data layer (Week 1)

**Goal:** accurate stats for every card in your deck plus towers and arena.

- [ ] Choose a data source and **write down where each number came from**:
  - Community-maintained datasets (e.g. RoyaleAPI's open card data, wiki tables). Easiest, but verify against in-game values.
  - Your own measurements from recordings of real matches.
  - Check the license/terms of whatever source you use before redistributing the data in your repo.
- [ ] For each card, capture at minimum:
  - Elixir cost, hitpoints, damage, hit speed, load time, deploy time
  - Movement speed, range, sight range, target type (ground/air/buildings only)
  - Collision radius, mass, unit count (swarms), spawn pattern
  - Special behavior flags (splash radius, charge, death spawn, lifetime for buildings)
- [ ] Pick one **tournament-standard level** (everything at the same level) to avoid level-scaling complexity at first.
- [ ] Add tower data: princess and king tower HP, damage, hit speed, range, king activation rules.
- [ ] Add arena data: dimensions in tiles, river, bridges, legal deploy zones (including the extra zone after a princess tower falls).
- [ ] Store everything as plain JSON/CSV in `data/` with a loader module and a schema check.
- [ ] Write tests that load every card in your deck and assert sane values (non-zero HP, positive speeds, etc.).

**Key design decision (make it now):** **use integer units everywhere.** Hasty-CR uses *millitiles* (1 tile = 1000) and **50 ms ticks** because every timing in the game data is a multiple of 50 ms. Convert all times to ticks and all distances to millitiles at load time. This makes the sim deterministic with zero floating-point drift.

**Done when:** a test prints a clean stat table for your 8 cards and all values are integer ticks/millitiles.

---

## Phase 3: Simulator core (Weeks 2-3)

**Goal:** a deterministic engine that can run a full match with *placeholder* behavior.

Build the tick loop with a **fixed phase order** (copy this idea; it's what makes replays diffable):

1. Scheduled effects (delayed spells, spawns)
2. Deploy (units finishing their deploy timers)
3. Targeting
4. Attack
5. Movement
6. Collision
7. Cleanup (deaths, death effects, removals)

Tasks:

- [ ] `Arena`: tile grid, walkable cells, river/bridge handling.
- [ ] `Entity` base class: id, team, position (int), HP, radius, state.
- [ ] `Troop`, `Building`, `Tower`, `Spell`, `Projectile` types.
- [ ] Elixir system: regeneration rates (including double/triple elixir if you want full matches), spending, cap at 10.
- [ ] Card cycle: 8-card deck, 4-card hand, next card, rotation rules.
- [ ] Match timer and win conditions (crowns, tower HP tiebreak, overtime if you want it).
- [ ] A single seeded RNG object passed everywhere. **No global randomness.**
- [ ] Event log: every phase emits normalized events (`deploy`, `attack`, `damage`, `death`...). You'll use this for debugging, replay, and calibration later.
- [ ] A minimal **renderer** (matplotlib or pygame) with a debug skin that draws **collision radius and attack range rings** for every unit. Build this early. Hasty-CR found a permanent body-block deadlock that was invisible without the rings.

**Done when:** two dummy policies can play a full 3-minute match and the *same seed produces a byte-identical event log* on two runs. Add that as a test.

---

## Phase 4: Implement your deck's cards, easiest first (Weeks 3-5)

**Goal:** all 8 cards behave correctly in isolation.

Order the work by difficulty. For **each card**, do this loop: implement → write a test → watch it in the debug renderer.

- [ ] Towers (needed for everything).
- [ ] Simplest ranged and melee troops.
- [ ] Swarm/multi-unit cards (spawn offsets, individual HP).
- [ ] Direct-damage spells (radius, crown tower damage reduction).
- [ ] Buildings (deploy time, lifetime decay, pull/targeting radius).
- [ ] Anything with splash, death effects, or special targeting.
- [ ] **Last:** the hardest card in your deck (charging, channeling, etc.).

For every card, write tests in the style "*one file per behavior, each named for the failure it prevents*":

- [ ] Stat sanity (HP, damage, speed match data).
- [ ] Targeting (what does it attack first? air vs ground? buildings only?).
- [ ] Timing (first hit lands on the right tick after deploy).
- [ ] Interaction tests: your card vs each likely counter and each likely opponent card.

**Mechanics that commonly cause bugs** (budget extra time):

| Mechanic | Typical failure |
|---|---|
| Unit-vs-unit collision | One cheap unit permanently blocks a tank or a charger ("deadlock") |
| Lane commitment | A unit whose lane tower fell walks to the wrong target |
| Targeting priority | Troops hitting buildings/towers when they should hit units, or vice versa |
| Splash & area damage | Off-by-one-radius, friendly-fire mistakes |
| Charging units | Damage multiplier and stop conditions |
| Spawner timing | First spawn tick, spawn offsets |

If you can't get a mechanic exactly right yet, **simulate it simply and write it into `docs/KNOWN_LIMITATIONS.md`** with how wrong you think it is. Don't leave it implicit.

**Done when:** all 8 cards pass their isolation tests, and `python -m sim.check` (see below) prints sensible predictions.

---

## Phase 5: Sanity-check tools (Week 5-6)

**Goal:** a way to ask the engine "what do you predict?" and compare against the real game.

- [ ] `sim/check.py`: prints concrete, testable claims, e.g. *"my tank on an undefended princess tower connects 5 times before dying"*, *"my ranged unit vs. Cannon wins after X seconds."*
- [ ] **Go play the real game** (or watch replays) and check at least 10 of those claims. Where they disagree, **the simulator is wrong.**
- [ ] `scripts/probe_mechanics.py`: card cycle enforcement, elixir economy, lane commitment, building pull radius, each printed as *measurement next to expectation*.
- [ ] Fix discrepancies, add a regression test for each fix.

**Done when:** you've verified at least 10 predictions against real gameplay and logged discrepancies in `docs/DECISIONS.md`.

---

## Phase 6: Rule-based baseline bot (Week 6-7)

**Goal:** a hand-written opponent *and* a training teacher.

- [ ] Write a simple rules policy for your deck: when to play each card, where, elixir thresholds, defend vs. attack logic.
- [ ] Also write trivial opponents: `random` and `simple` (play any affordable card at a random legal tile).
- [ ] Build 3-5 **meta opponent decks** with simple policies so you can test generalization. Hasty-CR evaluates against "meta decks" as well as its own rule engine for exactly this reason.
- [ ] `sim/batch.py`: headless parallel match runner (multiprocessing), deterministic per seed. Output win rate and crown differential.
- [ ] Measure: your rules bot vs random, vs simple, vs meta decks, 200+ matches each.

**Done when:** your rules bot clearly beats `random` and `simple` (target 90%+). If it can't, the sim or the rules have a bug. Debug *now*.

---

## Phase 7: Gym-style environment (Week 7-8)

**Goal:** a clean RL interface. **This is the contract between simulator and agent, so design it carefully.**

- [ ] **Observation:** stacked spatial planes, e.g.
  - Friendly/enemy troop HP-weighted occupancy per tile (separate planes for ground/air if relevant)
  - Building planes, tower HP planes
  - Plus a scalar vector: elixir, hand card identities, next card, time remaining, tower states
- [ ] **Action space:** discrete and **masked**. Hasty-CR uses `1 + 4 × N_tiles` (pass, or one of 4 hand slots on one legal tile). Compute a mask each step (enough elixir? legal tile? valid card slot?) and apply it before the softmax.
- [ ] **Reward** (start simple, tune later):
  - Large +/- for win/loss
  - Medium for crown differential
  - Small shaping for tower damage ("chip") and elixir efficiency
- [ ] **Vectorized envs:** run 8+ environments in parallel processes.
- [ ] Decision frequency: don't ask the agent for an action every 50 ms. Use a decision interval (e.g. every 4-10 ticks) with "pass" as a legal action.
- [ ] Put the obs/action definition in **one file** (`sim/env.py`). Everything else imports from it.

**Done when:** a random-masked-action agent runs thousands of steps without crashing and never takes an illegal action.

---

## Phase 8: Behavior cloning (Week 8-9)

**Goal:** a policy that already plays decently *before* PPO starts.

Hasty-CR's lesson: PPO from random init in a ~2,000-action space explores for a very long time before it ever wins.

- [ ] Generate a dataset by running your rules bot (against varied opponents) and recording `(observation, action, mask)`.
- [ ] Build the network: small CNN over the planes + MLP over scalars → policy head (masked logits) + value head.
- [ ] Train by cross-entropy against the rules bot's actions.
- [ ] Evaluate the clone vs. the rules bot, `random`, and meta decks.

**Gotcha to remember:** if you train *only* the action head in cloning, the **value head is random**. You'll need a *value warm-up* in PPO (Phase 9), or the first updates will wreck your good policy.

**Done when:** the clone is at least roughly competitive with the rules bot (it doesn't need to beat it).

---

## Phase 9: PPO training (Weeks 9-11)

**Goal:** an agent that surpasses the rules bot.

- [ ] Implement PPO (or adapt a trusted implementation) with action masking.
- [ ] Initialize from the clone checkpoint.
- [ ] **Value warm-up:** freeze the policy for the first N steps (Hasty-CR uses 300k) and train only the critic.
- [ ] **Target-KL early stopping** (~0.02): stop PPO epochs for a rollout once the policy has moved too far.
- [ ] **Opponent mix:** *this is not optional.* Train against a blend of meta decks and your rules bot (e.g. 50/50). Hasty-CR measured:

  | Trained against | vs rules bot | vs meta decks |
  |---|---|---|
  | meta only | 16.7% | 82.5% |
  | 50/50 mix | 93.3% | 86.7% |

  A policy that beats one opponent can be near-useless against another.
- [ ] Entropy bonus with an anneal schedule (explore early, exploit later).
- [ ] Log: win rate, crown diff, entropy, KL, value loss, and **behavior stats** (see Phase 10).
- [ ] Save checkpoints often, and **verify each loads** after saving.
- [ ] Optional later: self-play league (past checkpoints as opponents).

**Done when:** a 1-2M step run improves held-out win rate over the clone against *both* the rules bot and meta decks.

---

## Phase 10: Training supervisor (Week 11-12)

**Goal:** long unattended runs that don't silently get worse.

Long runs fail in a way that looks identical to success: numbers keep printing but the policy is worse than where it started.

- [ ] Track **behavior metrics**, not just loss, because they move before win rate does:
  - Share of plays per card (does it spam one card?)
  - Plays per match (is it passing too much?)
  - Average elixir at end of match
  - Score drift vs. a fixed reference opponent
- [ ] `scripts/rl_supervisor.py`: on a trigger (metric leaves a band, win rate drops), stop → roll back to the last **verified-loadable** best checkpoint → lower a hyperparameter (LR, KL target, entropy) → restart.
- [ ] Run a periodic **held-out audit** (fresh seeds, never trained on). If it regresses, roll back.

**Done when:** you can leave a 6-hour run alone and come back to a checkpoint at least as good as the one you started with.

---

## Phase 11: Evaluation and exploit hunting (Week 12-13)

**Goal:** know whether the win rate means anything.

- [ ] `scripts/evaluate_pilot.py`: one checkpoint vs. every opponent, 60+ held-out episodes each, fixed seeds, greedy actions. Report Wilson confidence intervals.
- [ ] `scripts/head_to_head.py`: two checkpoints, same deck, same seeds.
- [ ] `scripts/exploit_probe.py`: look for degenerate strategies:
  - Wins that depend on one card, one tile, or one timing
  - Win rate collapsing when you perturb a single parameter (spawn offset, a card's HP ±5%)
  - Games decided in the first 10 seconds
- [ ] Remember the caveat: **a simulated win rate is the simulator marking its own homework.** The most informative test is *you* playing a match against the agent in the sim (or watching it) and looking for dumb behavior and sim bugs.

**Done when:** you hit your Phase 0 success definition on held-out seeds **and** the exploit probe finds nothing alarming.

---

## Phase 12: Calibration against the real game (ongoing)

**Goal:** shrink the sim-to-real gap.

- [ ] Record real matches (screen recordings) featuring your deck.
- [ ] Extract key timings by hand: deploy → first hit, tower damage counts, spell timings.
- [ ] Replay the same situations in the sim and diff the event logs.
- [ ] Keep a ranked list of divergences in `docs/KNOWN_LIMITATIONS.md`, and fix them from largest impact to smallest.
- [ ] After each engine fix, **re-run your evaluation on the same checkpoint and seeds.** If numbers don't change, great; if they do, retrain.

---

## Phase 13 (OPTIONAL): Live play bridge

> ⚠️ **Read first:** automating Clash Royale is against Supercell's Terms of Service and can get your account banned. Hasty-CR itself says to treat this as a learning exercise. If you do it, use a throwaway account, friendly battles only, and never use it to gain ladder advantages.

If you proceed:

- [ ] Android emulator at a fixed resolution + screen capture.
- [ ] Object detection (YOLO) to read troops/cards/elixir from frames. You'll need to label your own dataset for your deck's cards.
- [ ] **Observation bridge:** convert detections into *exactly the same planes* the simulator produces. Write a test (`test_rl_policy.py`-style) that proves the live observation builder matches the sim's format. If these differ silently, the agent plays badly and no log will tell you why.
- [ ] Tap injection (ADB) mapped from your action space to screen coordinates.
- [ ] Known weak point: vision can't read unit HP, so units look full-health to the policy.

---

## Phase 14: Polish and write-up

- [ ] README with: install, quick-start commands, results table, architecture diagram, **known limitations section**.
- [ ] Showcase video/GIF of the sim (debug skin looks great and is informative).
- [ ] Clear "honest results" note: sim win rate ≠ real-world strength.
- [ ] Add a license, and a trademark disclaimer that Supercell is not affiliated.

---

## Suggested timeline

| Weeks | Phases | Milestone |
|---|---|---|
| 1 | 0-2 | Repo, data loaded, integer units |
| 2-3 | 3 | Deterministic empty-match engine |
| 3-6 | 4-5 | All 8 cards implemented + sanity-checked |
| 6-8 | 6-7 | Baseline bot, batch runner, RL env |
| 8-9 | 8 | Behavior clone |
| 9-12 | 9-10 | PPO + supervisor |
| 12-13 | 11 | Evaluation + exploit hunting |
| 13+ | 12-14 | Calibration, polish, optional live play |

Part-time, expect roughly 3-5 months. A simple deck with no charging units can be much faster.

---

## Lessons from Hasty-CR to keep taped to your monitor

1. **Integer physics + fixed ticks** = reproducible results. Do it from day one.
2. **Build the debug renderer with hitbox/range rings early.** Bugs you can't see, you can't fix.
3. **Behavior clone first, PPO second**, and **warm up the value head** before PPO touches the policy.
4. **Always train against a mix of opponents**, or you'll overfit to one.
5. **Watch behavior metrics, not just loss**, in long runs.
6. **Evaluate on held-out seeds against opponents the agent never saw.**
7. **One test file per behavior, named for the failure it prevents.** Use `xfail` for known bugs so they can't be quietly forgotten.
8. **Write down every approximation.** An honestly documented limitation beats a hidden one.
9. **Re-measure after engine fixes** instead of assuming results still hold.
10. **The simulator is the thing that's wrong** whenever it disagrees with the real game.

---

## Quick checklist (copy into your issue tracker)

- [ ] Deck chosen, scope + success criteria written
- [ ] Repo skeleton + CI running `pytest`
- [ ] Data loaded (integer ticks/millitiles) with sources recorded
- [ ] Deterministic tick loop, seeded RNG, event log
- [ ] Debug renderer with hitbox/range rings
- [ ] All 8 cards implemented with tests
- [ ] 10+ sim predictions verified against the real game
- [ ] Rules bot beats random/simple 90%+
- [ ] Gym env with masked actions, vectorized
- [ ] Behavior clone trained
- [ ] PPO with value warm-up, target-KL, opponent mix
- [ ] Supervisor with rollback
- [ ] Held-out evaluation + exploit probe
- [ ] Calibration log + known limitations doc
- [ ] (Optional) live bridge, with ToS caveat acknowledged
- [ ] README, results, honest caveats
