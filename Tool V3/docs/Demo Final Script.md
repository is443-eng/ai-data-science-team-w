# Demo Final Script — Measles Dashboard (transcript-aligned)

This version **follows what you said on the recording** (`Demo Raw Transcsript.txt`, ~11:07:20–11:14:11), tightened for readability. Use it if you want the **spoken voice**, not the rubric-style talking-points doc.

**Deployed app:** https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/

**Filming cue (Jonathan, pre-roll):** *“We don’t need to spend too long on any slide—we just want to show them everything.”*

---

## Count-in

**Jonathan:** Recording in three… two… one…

---

## Open & Overview

**Jonathan** · *Overview / landing.*

Alright—good morning, everybody. My name is **Jonathan Lloyd**, here with **Ian Steigmeyer**. We’re going to present our interactive dashboard on **measles outbreak data in the United States**.

This website was deployed to our **Posit Cloud** server. This is our **third iteration**.

We’ll start on the landing page, the **overview** page, because we want to **generate this insight**. I’m going to **start running it now**—it takes about **thirty seconds** sometimes.

The **baseline risk** is **high / medium / low**, **bucketed with scores**. This baseline risk is calculated from **all of our datasets combined**: we’ve got **historical trends** that use **CDC data** for **cases over time**, **kindergarten vaccination coverage**, and **wastewater testing indicators**—all of that **feeds the score**. As you can see we’re at **72**—we’re in the **red zone**. If you’ve looked at the news lately, there are **cases going on across the country**, so **this does make sense**.

To **generate insights** from the data for **particular states of concern**—for example **Idaho**, which has **low vaccination rates**—if I’m a **parent in Idaho**, or maybe a **CDC administrator**, and I’m trying to get **quick insights** without doing a bunch of **forensics**, you can **run this report**. It gives you an **AI-generated summary**.

This also has **quality control** built in, in an **agentic loop**. We’ve got **QC metrics** running in the background—it’ll **loop up to about three times** if needed, so the output **isn’t hallucinated** and is **good quality** for useful insights.

As you can see here, **both of these passed on the first quality try**—**five out of five**, love to see that.

**Meanwhile**, like I mentioned, **Idaho is high risk**—it’s got a **composite risk score**, and **Ian will talk a little more about that score** later on.

We’ll move on to the next page.

**Refresh (from rehearsal—say on Overview if you still want it):** At any time you can **refresh the data**; it’ll pull fresh if the data is **older than about an hour**.

---

## Historical trends

**Ian** · *After transition to **Historical trends**.*

I wanted to add: the **source of the data is the Socrata API**—**all of the datasets** are accessed with an **API key for Socrata**.

**Jonathan:** Great point, thank you.

**Ian**

So this is the **historical trends** page. The **first page** is meant to be—if you’re **only going to see one page** on the site—that’s meant to be the **overview**: you kind of get **what you need** there.

But if you’re curious about **more detail**, these **other pages** **break out the different datasets**. This first one shows **historical trends of measles cases**.

You can see both a **longer-range**, **yearly** picture—which is **what Jonathan was pointing at** there—and **more recently**, over roughly the **last couple of years**, how cases have **trended**.

Yeah—and you can look at a **weekly view for each individual year**.

---

## Kindergarten coverage

**Jonathan** · *On **Kindergarten coverage**.*

Alright—so the **next dataset we pulled from Socrata** was **kindergarten MMR vaccination coverage**. This dataset has information from **2009 through 2024**, when **data collection seemed to start to lapse**.

This is a straight **percent coverage** score, visualized **here on the map**. As you can see, **Idaho’s not looking so great**. Some states have **data unavailable**, but generally you get **really varying shades of blue**. **This coverage feeds some of the other risk scores.**

---

## Wastewater vs NNDSS

**Ian** · *On **Wastewater vs NNDSS**.*

This is **one of the most interesting datasets** for tracking measles. It looks at detection of **MMR RNA** in the **wastewater system**.

So it’s actually a **precursor**—almost a **forecasting indicator** for **measles outbreaks**. That’s **one factor in our risk score**: **detection of MMR RNA in wastewater**.

This chart compares **MMR detection in wastewater** with the **number of cases**. *On this view it looks **annual**,* but we also have data **by state**, and yeah—you **can select which state** you want to look at.

**Jonathan:** We’ve also got a **dedicated AI reporter** here—the same idea as **some of the other pages**—so you can get **more targeted insights** on **specific datasets** you care about.

---

## State risk

**Jonathan** · *On **State risk**.*

**State risk**—**same idea**: there’s a **state AI reporter**, but mainly this **combines at state level what the risk score might be**.

You’ve got the **case count**, **wastewater data**, and **coverage**, and **whether you have wastewater coverage or not**. You can see **Utah**—not looking so great. **Oregon**—not looking so great—**ranked by score**.

**That feeds the forecasting page—that’s where Ian kind of rolls it all up.**

*(Optional: gesture at **how state risk is calculated**—you mentioned coverage + cases + wastewater in rehearsal.)*

---

## Forecast & sign-off

**Ian** · *On **Forecast**.*

Yeah—the **forecasting page** shows **which states have the highest risk of an outbreak**—or honestly it shows a **score for every state**—but it’s **really useful** for seeing **which states are having an outbreak right now**.

On the **right**, there’s an explanation of the **main factors driving the score** for each state—**lots of recent cases**, **MMR in the wastewater**, or **low vaccination rates**—that shows up in the **column on the right**.

There’s also an **AI reporter** that gives information about **which states are at the highest risk** and **what’s causing that**.

**Jonathan:** Alright—that’s our app. Thank you all very much. Hope you enjoyed it, and hope you were able to get some **useful insights** out of this.

**Ian:** Great. Thank you.

---

## Light polish only (optional)

| If you said this on tape… | You can fix on re-record… |
|---------------------------|---------------------------|
| “Stegmaier” | **Steigmeyer** |
| “Posit Cloud” | **Posit Connect** (only if graders expect the Connect name) |
| “Mary” | **Meanwhile** |
| “historical traps” | **historical trends** |
| “MNR” | **MMR** |

Keep the **Idaho / Utah / Oregon** callouts—they’re exactly what landed on camera.
