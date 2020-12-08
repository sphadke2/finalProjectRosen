# Intro and video link

I've shared my CS50 IDE with Professor Rosen, so to view it go to this link https://ide.cs50.io/sphadke2/ide.

To run it from there you must first cd into the final project folder, use control-r to look up export API key ...., (just type in exp should show up),
then type the command flask run

It should give you a link to open.

--Video Link

https://youtu.be/aM_QWCvgmOk

--Note
The main file(s) that do the heavy lifting are application.py and MonteCarlo.py.

## High level overview of modfications to the finance CS 50 application

-- Main changes made: data is no longer pulled using API, I supply the option chain data. The option chain is calculated using a function in the MonteCarlo.py file.
The options are calculated with a random walk stock price model.

-- Other changes on the front end are including dropdowns for the limited stock selections and strike price selections.

-- In addition, the sell price is determined by taking the final stock price from one of the 10,000 simulated stock prices and determining the value of the contract in that particular scenario. For example you bought a 150 strike Apple Call for $35.00. Let's say the year ahead forcasted price is 300. That means the value of the contract is $150.00. the displayed sell price is the value of the contract, $150.00.

--Often the value of the sold option is $0.00, as the forecasted stock price is below the strike price.


### Things Learned / difficulties
-- Learned how to modify web applications, using get and post methods
-- Learned how to create a simple option pricing model, using a monte carlo simulation (Part I had the most fun with)

--Difficulties

-- Deciding how the scope of the project had to change. Initially wanted to do calls and puts. Settled on just calls. However, while coding thought about how I'd have to modify existing code to allow for puts as well. Would most likely need to create new functions for generating put prices, or could add another parameter into the generating_option_chain functions that would handle both calls and puts.

-- Did not run into too many difficulties after this, as I spent a lot of time thinking about how I would have to modify existing code. When I got to actually coding it, went very very somothly.

