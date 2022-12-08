# SETUP # -----------------------------------------------------------------------
print("---------- SETUP ----------")
import mysql.connector
import gurobipy as gp

# DB Connect
pwd = input("Database Password:")
con = mysql.connector.connect(host='localhost', database = 'nasdaq', user = 'root', password = pwd)

# DB Utility Functions (from StackOverflow)
def query_with_fetchone(query):
    i = 0
    try:
        cursor = con.cursor(buffered = True)
        cursor.execute(query)        
        return cursor.fetchall()
    except Exception as e:
        print(e)
    finally:
        cursor.close()

def insert_varibles_into_table(expReturn, expRisk):
    try:
        cursor = con.cursor()
        mySql_insert_query = "INSERT INTO portfolio (expReturn, expRisk) VALUES (%s, %s)"
        record = (expReturn, expRisk)
        cursor.execute(mySql_insert_query, record)
        con.commit()
        print("Row sent.")

    except mysql.connector.Error as error:
        print("Failed to insert into MySQL table {}".format(error))



# Fetch Data # ------------------------------------------------------------------
print("---------- FETCH ----------")

# Fetch Data
cov_initial = query_with_fetchone("SELECT * FROM cov;")
Q = {(item[0], item[1]):item[2] for item in cov_initial}

r_initial = query_with_fetchone("SELECT * FROM r;")
r = {item[0]:item[1] for item in r_initial} #r = a
stock_names = [*r.keys()]



# Structure Sanity Check # ------------------------------------------------------
print("---------- SANITY CHECK ----------")

# Inputs
covs = [[0.04, 0.018, 0.0064],
        [0.018, 0.0225, 0.0084],
        [0.0064, 0.0084, 0.0064]]
weights = [0.5, 0.0, 0.5]
covs_dict = {(stock1, stock2):covs[stock1][stock2] for stock1 in range(len(covs)) for stock2 in range(len(covs[1]))}
    #[Row, Column]

# Output
sum(weights[stock1] * covs_dict[(stock1,stock2)] * weights[stock2] for stock1 in range(len(covs)) for stock2 in range(len(covs[1])))
    #0.0148, matching "solver.xlsx"!
    


# Model Loop # ---------------------------------------------------------
print("---------- GUROBI LOOP ----------")

results = []
for maxRisk in [i / 100 for i in [*range(1, 101)]]: #MAKE 101
    print(f"ITERATION MAXRISK: {maxRisk}")
    
    # Setup
    m = gp.Model("Portfolio")
    
    # DECISION: Investment Weights
    investment_weights = {stock:m.addVar(vtype = gp.GRB.CONTINUOUS, lb = 0, ub = 1, name = f"%inv_in_{stock}") for stock in stock_names}

    # OBJ: Max Return
    m.setObjective(gp.quicksum(investment_weights[stock]*r[stock] for stock in stock_names), gp.GRB.MAXIMIZE)

    # RESTRAINTS: Invest everything.  
    m.addConstr(sum(investment_weights.values()), gp.GRB.EQUAL, 1, "Invest everything.")
    m.addConstr(gp.quicksum( investment_weights[stock1] * Q[(stock1,stock2)] * investment_weights[stock2] for stock1 in stock_names for stock2 in stock_names), gp.GRB.LESS_EQUAL, maxRisk, "Variance Max")

    # Update
    m.update()

    # Attempt Optimization 
    m.optimize()

    try:
        results.append((maxRisk, m.ObjVal, sum(investment_weights[stock1].X * Q[(stock1,stock2)] * investment_weights[stock2].X for stock1 in stock_names for stock2 in stock_names)))
    except Exception as e:
        results.append((maxRisk, 0, 0))

    if len(results) >= 3 and results[-1][1] != 0:
        if results[-1] == results[-2] == results[-3]:
            print("NOT CHANGING")
            break

print(f"Results: {results}")

for tup in results:
    insert_varibles_into_table(tup[1], tup[2])
