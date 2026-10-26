---

## Slide title

**What the data tells us: a few signals stand out**

## Starting point: the data we looked at

Four number cards in a slim strip directly under the title:

- **135,493 clients** with known fraud result (plus 58,069 more clients that we use for the final test)
- **4.5 million bills**, about 30 per client
- **22 facts** about clients and bills: 6 per client (region, client category, start date, ...) and 16 per bill (date, price plan, meter, consumption, ...)
- **Goal: find the clients with fraud.** We summarise each client's bills into one picture per client.

## Block A: Fraud is rare

- **Only 5.6% of clients are fraud** (about 1 in 18).
- Why it matters: if we said "no fraud" for everyone, we would be right 94% of the time, and find nobody.
- So we measure success differently: **how well we rank clients** (who to visit first), not how often we are right.

## Block B: Which signals go with fraud?

Horizontal bar chart. Chart title: **"Share of clients with fraud, by signal"**. One bar per signal, longest on top, value label at the end of each bar, no table. Dashed vertical line = **"Average of all clients: 5.6%"**. Bar colour = topic (add a small colour legend: Meters and meter setup, Billing activity and history, Consumption, Client profile). Caption: *Each bar shows the share of fraud among clients with this striking trait. Links in the data, not proof of cause.*

```
Number of meters (replaced meter): 4 or more   ████████████████████ 20.2%  (blue)
Different meter codes used: 3 or more          ██████████████████▌  18.5%  (blue)
Client category 51                             ████████████████▊    16.9%  (grey)
Biggest single bill: 10,000 to 50,000          █████████████        13.2%  (green)
Meter reading goes backward                    ███████████          11.3%  (blue)
Region 103                                     ██████████           10.3%  (grey)
Gas: ups and downs in use (most unsteady)      █████████            9.1%   (green)
Number of bills: 51 or more                    █████████            9.0%   (orange)
Total consumption (highest 25% of clients)     ████████             8.4%   (green)
                                               ┆ average of all clients: 5.6%
```

Small note under the chart: "Biggest single bill" = the largest bill of a client, in consumption units.

## Block C: Three signals up close

**1. Number of meters** (the strongest signal)

- Fraud share: **2.1%** with 1 meter, 6.2% with 2, 14.8% with 3, **20.2%** with 4 or more.
- Example: like a car whose odometer was swapped several times. Something may be going on.

**2. Gas: ups and downs in use**

- Fraud share: **5.1%** for the steadiest gas clients, **9.1%** for the ones whose use jumps the most.
- Example: one household heats steadily all winter, another one's gas use jumps up and down.

**3. Meter reading goes backward**

- Fraud share: **11.3%** vs 5.5% for all other clients. Rare: only 1,816 clients.
- Example: an odometer that runs backward.

## Closing line (highlight box)

**Result of our first look at the data: these signals (meters and meter setup, billing activity and history, consumption, client profile) move on to the next step, the machine learning cycle.**

---

## Speaker notes (optional)

### What to say about the chart (about 2 minutes)

*Intro:* "On average, 5.6% of our clients are fraud, that is the dashed line. Each bar shows how often clients with one striking trait are fraud. The longer the bar, the more it is worth looking at these clients first. These are links in the data, not proof of cause."

1. **Number of meters, 4 or more (20.2%).** "Most clients have one meter, and only 2.1% of them are fraud. With every extra meter the share rises: 6.2% with two, 14.8% with three, and 20.2% with four or more. A meter that was swapped several times can be a sign of tampering. It can also be STEG's reaction after it found fraud. We should ask STEG."
2. **Different meter codes used, 3 or more (18.5%).** "Clients who have used three or more different meter codes are fraud in 18.5% of cases, clients with only one code in just 3.3%. A changing meter setup is unusual, and it goes with fraud."
3. **Client category 51 (16.9%).** "STEG sorts clients into categories. Category 51 has 16.9% fraud, while category 11, the most common one, has 5.5%. So the type of client already tells us where to look."
4. **Biggest single bill, 10,000 to 50,000 (13.2%).** "The bigger the largest bill of a client, the more often it is fraud: 2.6% when the largest bill is below 1,000, and 13.2% when it is between 10,000 and 50,000. Above 50,000 the share drops again to 3.8%. These are probably typing errors, not real bills."
5. **Meter reading goes backward (11.3%).** "A meter normally only counts upward, like an odometer. When a reading is lower than the one before, something is off. These clients are fraud in 11.3% of cases, about twice the average. It is rare: only 1,816 clients. Some are harmless, for example when a meter restarts after reaching its maximum."
6. **Region 103 (10.3%).** "Fraud is not spread evenly. In region 103 it is 10.3% and in region 311 it is 8.0%. In regions 101 and 301 it is only about 3%."
7. **Gas: ups and downs in use, most unsteady (9.1%).** "Some gas clients use gas steadily, others jump from very little to a lot between bills. Among the steadiest it is 5.1% fraud, among the most unsteady 9.1%. Steady use is normal, strong jumps are worth a closer look."
8. **Number of bills, 51 or more (9.0%).** "The longer a client has been in our records, the more bills they have. Clients with 51 or more bills are fraud in 9.0% of cases, clients with 1 to 10 bills in only 1.3%. Part of this is simply that fraud has more time to be found."
9. **Total consumption, highest 25% of clients (8.4%).** "Clients who consume the most are fraud in 8.4% of cases. Among the quarter with the lowest consumption it is only 1.2%."

*Wrap-up:* "No single signal proves fraud. Together they give us a first picture. In the next step, the machine learning, we let the computer combine all of them into one priority list."

### More notes

- Starting point: we have two lists. One has one line per client (including whether the client was found to be a fraud). The other has one line per bill, about 30 per client. The 58,069 extra clients come without the fraud result. They are used to test our work at the end. Every client has bills, so nobody is lost when we combine the lists.
- Terms: "different meter codes used" = the different meter codes a client has had. "Client category" = the customer type in STEG's data. "Units" = the consumption numbers as they appear on the bills. Chart names follow the names we use throughout the project.
- 5.6% fraud means simple "how often are we right" is misleading. We need a "priority list": STEG can only inspect a limited number of homes, so ranking matters.
- The chart shows fraud shares per group. These are links in the data, **not proof of cause**.
- Careful with the meter signals: a replaced meter may partly show what STEG did *after* it found fraud. Our data has no date of detection. We should ask STEG how this comes about.
- Another striking group (not in the chart): clients whose last bill is more than 5 years old are fraud in only 0.7% of cases (vs 6.5%). These are probably closed accounts nobody inspects.
- Sources: 05_eda-summary.md and 03_eda-analysis.ipynb. The "3 or more different meter codes" figure comes from the later error analysis.
- For the next slide: the final model reaches a ranking quality (ROC-AUC) of 0.876 in cross-validation and 0.874 on the Zindi test set (0.5 = coin flip, 1.0 = perfect; our first simple model: 0.76).
