All data is from current version of Clash Royale app (Current version: 160402020)
All cards in deck including king tower and princess towers are at level 11

Speed Tier - In-game value - Tiles/sec
Slow - 45 - 0.75
Medium - 60 - 1.00
Fast - 90 - 1.50
Very Fast - 120 - 2.00

Melee Range tier
Melee: Short - 0.8 tiles
Melee: Medium - 1.2 tiles
Melee: Long - 1.6 tiles

First Hit Time = Hit Time − Load Time

Load Time = Hit Time − First Hit Time

## Royal Recruits

-Shield Hit points: 240 (per recruit)
-Elixir: 7
-Hitpoints: 547 (per recruit)
-Damage: 133 (per recruit)
-Hit speed: 1.3secs
-First Hit Speed: First hit on the 10th tick after deploy completion
-Sight Range: 5.5 tiles
-movement speed: Medium
-Range: Melee Long
-Deploy Time: 1 sec
-Load Time: 0.8 secs
-Target Type: all ground troops, buildings and towers
-Unit count: 6
-spawn pattern: Across 15000 millitiles middle tile being placement cursor ((-7000,0), (-4000,0), (-500,0), (+500,0), (+4000,0), (+7000,0))millitiles
-Collision Radius: 0.5 tiles
-Mass: 5
-splash radius: 0
-death spawn: 0
-lifetime: 0
-projectile: 0

Special Flags:
-When recruits are being placed they stay in the horizontal line and cannot be compressed or slid inwards and the center tile indicator for recruits placement can only be played +-2000millitiles on the x axis on your side of battle arena which is everything on the negative side of the y axis.
-When recruits are being placed at either edge limit of the battle arena the recruit at the (+7000,0) and (-7000,0) positions stop the other units from being grouped up or going out of bounds before deployment.
-Shields take 240 Damage and fall off leaving just Recruit hit points
-Any single hit breaks the shield and all excess is discarded, regardless of size (applies to spells, splash damage and tower damage)
-Evo stats identical to base except for the charge behavior
-When in evo state the recruit charges only after losing the shield and moving 2500 from shield break position, if shield never breaks then charge can't happen
-When in evo state the recruit charges at 100 millitiles/tick
-When evo state is charging and hits target(buildings, towers, and units) for double the normal damage amount(2×133), or stunned(Electro wiz, ice spirit, electro spirit), or pushed back(log, bowler, fireball) the charge ends and the recruit needs to move 2.5 tiles to start new charge and if recruit evo is stopped before the 2.5 tiles the recruit is reset and needs to move 2.5 tiles to trigger charge
-When in evo state the recruit will continue to charge if the enemy unit is dead or leaves the recruits sight range
-When in evo state the charge can be slowed and the recruit still needs to travel the 2.5 distance to trigger charge but body blocking does not reset the 2.5 tile charge requirement(slow effects from too much mass in front of recruit stopping movement, ice wizard, ice golem hero ability)
-Evo state is same elixir cost as normal recruits
-Evo state charge is per recruit not the group
-Evo state charge hit triggers on contact

-Evo Recruit trigger States:
-Recruits start as normal
-Playing NORMAL recruits, then having the card re-enter the hand, makes it EVO_READY.
-While EVO_READY, every play is the evo version (no player choice).
-Playing the evo returns it to NORMAL, so you need another normal play and re-entry.
