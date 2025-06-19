## Beat the Market AI — Outsmart the Biased Manipulator

This is a decision-based trading game that simulates a biased market controlled by an intelligent adversary. Your role is to act as a trader and defeat the manipulative system by anticipating its traps and making smart trading decisions.

---

### Game Logic

The system simulates a trading environment where the price evolves over time as candlestick charts. Behind the scenes, an AI manipulator continuously observes your behavior and attempts to bias the market against your actions.

At every moment, you can:

* Enter a **Buy (Long)** position
* Enter a **Sell (Short)** position
* **Close** an existing position to realize gains or losses

Each choice influences not only your potential profit but also how the market manipulator reacts to you next.

---

### Simulation Flow

1. **Initialization**:

   * The game starts with a wallet of \$100.
   * A historical price chart is generated to give context.

2. **Live Market Generation**:

   * New price movements are added periodically.
   * Each new price point is shaped by two factors:

     * Random market noise
     * Strategic bias from the AI based on your trade history

3. **AI Strategy**:

   * The AI tracks your recent decisions (e.g., Buy-Buy-Buy, Sell-Sell, or alternating).
   * Once a pattern is detected, it adjusts market direction to work against your expected outcome.

     * For example: If you Buy repeatedly, the AI will push prices downward.
   * If you open a position and the market turns against you due to AI bias, you may fall into a trap.

4. **Trade Mechanics**:

   * When you **enter a position**, your entry price is recorded.
   * When you **close the position**, the outcome is calculated based on market movement and whether the AI was actively trapping you.
   * Escaping a trap successfully is counted as a strategic win.

5. **Game End**:

   * The game runs for a fixed time (e.g., 90 seconds).
   * Your final performance is evaluated based on:

     * Total wallet balance
     * Number of trades
     * Number of traps triggered vs. traps escaped

---

### Player Tips

* Avoid obvious trading patterns (e.g., constant buying).
* Think like a strategist — consider how your next action might be exploited.
* Even a few successful trades can lead to victory.
* Random or alternating strategies can confuse the AI and reduce bias.

---

### Learning Objective

This game models adversarial behavior in decision-making systems. It demonstrates how predictive systems can be exploited or defeated through awareness, unpredictability, and strategic thinking. It can be used to study:

* Behavioral patterns under manipulation
* Reward–punishment loops in adversarial systems
* Decision making under uncertainty
* How AI systems might simulate market bias

---

