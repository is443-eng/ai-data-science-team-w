# Step-by-step: Run the Measles Map Shiny App

Do these steps in order.

---

## Step 1: Get a CDC API token

1. Open a browser and go to: **https://data.cdc.gov/profile/edit/developer_settings**
2. Log in or create a free account if needed.
3. On the Developer Settings page, find **“App Token”**.
4. If you don’t have one, click **“Create new app token”** (or similar). Give it a name (e.g. “Measles map”) and create it.
5. **Copy the token** (long string of letters/numbers). Keep it somewhere safe — you’ll paste it in Step 2.

---

## Step 2: Put the token where R can see it

You’ll put the token in a file called `.Renviron` in your home folder so R can read it every time.

**Option A — Using R (easiest):**

1. Open **R** or **RStudio**.
2. In the R console, run:
   ```r
   usethis::edit_r_environ()
   ```
   If it says “package ‘usethis’ is not installed”, run:
   ```r
   install.packages("usethis")
   ```
   Then run `usethis::edit_r_environ()` again.
3. A file will open (often in RStudio). It might be empty or have a few lines.
4. On a **new line**, type exactly (paste your real token where it says `YOUR_TOKEN_HERE`):
   ```
   SOCRATA_APP_TOKEN=YOUR_TOKEN_HERE
   ```
   Example (fake token):
   ```
   SOCRATA_APP_TOKEN=AbCdEf123456XyZ
   ```
   No spaces around the `=`. No quotes around the token.
5. Save the file and close it.

**Option B — Using Finder / TextEdit (Mac):**

1. Open **Finder**.
2. Press **Cmd + Shift + H** to go to your Home folder (house icon).
3. If you don’t see a file named **`.Renviron`**:
   - Open **TextEdit**. Create a new file.
   - Type: `SOCRATA_APP_TOKEN=YOUR_TOKEN_HERE` (with your real token).
   - Go to **Format → Make Plain Text**.
   - Save As: **`.Renviron`** in your Home folder (choose “All Files” or “Don’t add extension” so it’s exactly `.Renviron`, not `.Renviron.txt`).
4. If you already have a file named **`.Renviron`**:
   - Right‑click it → **Open With → TextEdit** (or another editor).
   - Add a new line: `SOCRATA_APP_TOKEN=YOUR_TOKEN_HERE`.
   - Save and close.

**Then:** Fully quit R/RStudio and open it again so it loads the new token.

---

## Step 3: Install R packages the app needs

1. Open **R** or **RStudio** again (after restarting in Step 2).
2. In the R **console** (where you type commands), run this **one line** and press Enter:
   ```r
   install.packages(c("shiny", "leaflet", "dplyr", "sf", "tigris", "httr", "jsonlite", "scales"))
   ```
3. If R asks “Do you want to install from sources…?”, type **n** and press Enter (use the binary packages).
4. Wait until it finishes (can take a minute or two). When you see the `>` prompt again with no errors, you’re done.

---

## Step 4: Open your project folder in R

You need R’s “working directory” to be your project folder (the one that contains the `shiny_app` folder).

1. In R, run (replace with your real path if different):
   ```r
   setwd("/Users/mjt/Desktop/ai-data-science-team-w")
   ```
   To see where you are:
   ```r
   getwd()
   ```
   It should print something ending in `ai-data-science-team-w`.

**Or in RStudio:** use **File → Open Project** and open the `ai-data-science-team-w` folder (if it has an `.Rproj`), or **Session → Set Working Directory → Choose Directory** and pick `ai-data-science-team-w`.

---

## Step 5: Run the Shiny app

1. With your working directory set to `ai-data-science-team-w` (Step 4), run:
   ```r
   shiny::runApp("shiny_app")
   ```
2. A window or browser tab should open with the app. You should see:
   - A sidebar with a button: **“Load data from CDC API”**
   - A short message about loading data
   - A map (may be empty until you load data)

If you get an error like “cannot change working directory” or “shiny_app not found”, go back to Step 4 and make sure `setwd(...)` points to the folder that **contains** the `shiny_app` folder.

---

## Step 6: Load the data and use the map

1. In the app, click the button: **“Load data from CDC API”**.
2. Wait a few seconds. You should see a message like “Loaded … rows.”
3. In the sidebar you should now see:
   - **Year** (dropdown)
   - **MMWR Week** (slider 1–53)
4. Pick a **Year** (e.g. 2024) and a **Week** (e.g. 10).
5. The map should update and show US states colored by measles cases for that week (yellow = fewer, red = more). Hover over a state to see the count.

---

## If something goes wrong

- **“Set SOCRATA_APP_TOKEN…”**  
  R doesn’t see your token. Redo Step 2, then fully quit and reopen R, then try Step 5 again.

- **“No data returned”**  
  Token might be wrong or expired. Check Step 1 and Step 2 (no extra spaces, no quotes).

- **Package errors when installing**  
  Try installing one at a time, e.g. `install.packages("shiny")`, then `install.packages("leaflet")`, etc. If one fails, read the error; sometimes you need Xcode Command Line Tools (Mac) or Rtools (Windows).

- **App doesn’t open / “object not found”**  
  Make sure you ran `setwd("/Users/mjt/Desktop/ai-data-science-team-w")` (or your path) before `shiny::runApp("shiny_app")`.
