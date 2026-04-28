# %% [markdown]
# ## Introduction
#
# In this lab assessment, you'll practice your knowledge of JOIN statements and subqueries, using various types of joins and various methods for specifying the links between them.
#

# %% [markdown]
# ## Learning Objectives
#
# - Write SQL queries that make use of various types of joins
# - Choose and perform whichever type of join is best for retrieving desired data
# - Write subqueries to decompose complex queries
#

# %%
# CodeGrade step0
# Run this cell without changes

import sqlite3
import pandas as pd

conn = sqlite3.connect('data.sqlite')
pd.read_sql("""SELECT * FROM sqlite_master""", conn)

# %% [markdown]
# ## Part 1: Join and Filter
#

# %% [markdown]
# ### Step 1
#
# Return the first and last names and the job titles for all employees in Boston.
#

# %%
# CodeGrade step1
df_boston = pd.read_sql("""
    SELECT e.firstName, e.lastName, e.jobTitle
    FROM employees e
    JOIN offices o ON e.officeCode = o.officeCode
    WHERE o.city = 'Boston'
""", conn)

df_boston

# %% [markdown]
# ### Step 2
#
# Are there any offices that have zero employees?
#

# %%
# CodeGrade step2
# A LEFT JOIN keeps all offices; NULL on the employee side means no employees
df_zero_emp = pd.read_sql("""
    SELECT o.officeCode, o.city
    FROM offices o
    LEFT JOIN employees e ON o.officeCode = e.officeCode
    WHERE e.employeeNumber IS NULL
""", conn)

df_zero_emp
# Empty DataFrame means every office has at least one employee — no 'ghost' locations

# %% [markdown]
# ## Part 2: Type of Join
#

# %% [markdown]
# ### Step 3
#
# Return all employees' first and last name along with the city and state of their office. Include ALL employees and order by first name then last name.
#

# %%
# CodeGrade step3
# LEFT JOIN so employees without an office are still included
df_employee = pd.read_sql("""
    SELECT e.firstName, e.lastName, o.city, o.state
    FROM employees e
    LEFT JOIN offices o ON e.officeCode = o.officeCode
    ORDER BY e.firstName, e.lastName
""", conn)

df_employee

# %% [markdown]
# ### Step 4
#
# Return contact info and sales rep employee number for any customer who has NOT placed an order. Sort alphabetically by contact last name.
#

# %%
# CodeGrade step4
# LEFT JOIN customers -> orders; NULL orderNumber means no order was placed
df_contacts = pd.read_sql("""
    SELECT c.contactFirstName, c.contactLastName,
           c.phone, c.salesRepEmployeeNumber
    FROM customers c
    LEFT JOIN orders o ON c.customerNumber = o.customerNumber
    WHERE o.orderNumber IS NULL
    ORDER BY c.contactLastName
""", conn)

df_contacts

# %% [markdown]
# ## Part 3: Built-in Function
#

# %% [markdown]
# ### Step 5
#
# Return all customer contacts with their payment amounts and dates, sorted by payment amount descending.
#

# %%
# CodeGrade step5
# CAST amount to REAL to ensure correct numeric sort (stored as TEXT in this DB)
df_payment = pd.read_sql("""
    SELECT c.contactFirstName, c.contactLastName,
           p.paymentDate,
           CAST(p.amount AS REAL) AS amount
    FROM customers c
    JOIN payments p ON c.customerNumber = p.customerNumber
    ORDER BY CAST(p.amount AS REAL) DESC
""", conn)

df_payment

# %% [markdown]
# ## Part 4: Joining and Grouping
#

# %% [markdown]
# ### Step 6
#
# Return the employee number, first name, last name, and number of customers for employees whose customers have an average credit limit over 90k. Sort by number of customers (high to low).
#

# %%
# CodeGrade step6
df_credit = pd.read_sql("""
    SELECT e.employeeNumber, e.firstName, e.lastName,
           COUNT(c.customerNumber) AS num_customers
    FROM employees e
    JOIN customers c ON e.employeeNumber = c.salesRepEmployeeNumber
    GROUP BY e.employeeNumber
    HAVING AVG(CAST(c.creditLimit AS REAL)) > 90000
    ORDER BY num_customers DESC
""", conn)

df_credit

# %% [markdown]
# ### Step 7
#
# Return product name, count of orders as 'numorders', and total quantity sold as 'totalunits'. Sort by totalunits highest to lowest.
#

# %%
# CodeGrade step7
df_product_sold = pd.read_sql("""
    SELECT p.productName,
           COUNT(od.orderNumber)     AS numorders,
           SUM(od.quantityOrdered)   AS totalunits
    FROM products p
    JOIN orderdetails od ON p.productCode = od.productCode
    GROUP BY p.productCode
    ORDER BY totalunits DESC
""", conn)

df_product_sold

# %% [markdown]
# ## Part 5: Multiple Joins
#

# %% [markdown]
# ### Step 8
#
# Return product name, product code, and total distinct customers who ordered each product as 'numpurchasers'. Sort by highest purchasers.
#

# %%
# CodeGrade step8
# 3-table join: products -> orderdetails -> orders (which has customerNumber)
df_total_customers = pd.read_sql("""
    SELECT p.productName,
           p.productCode,
           COUNT(DISTINCT o.customerNumber) AS numpurchasers
    FROM products p
    JOIN orderdetails od ON p.productCode = od.productCode
    JOIN orders o        ON od.orderNumber = o.orderNumber
    GROUP BY p.productCode
    ORDER BY numpurchasers DESC
""", conn)

df_total_customers

# %% [markdown]
# ### Step 9
#
# Return the count of customers per office as 'n_customers', along with office code and city.
#

# %%
# CodeGrade step9
# Chain: offices -> employees -> customers (via salesRepEmployeeNumber)
df_customers = pd.read_sql("""
    SELECT o.officeCode,
           o.city,
           COUNT(DISTINCT c.customerNumber) AS n_customers
    FROM offices o
    JOIN employees e  ON o.officeCode      = e.officeCode
    JOIN customers c  ON e.employeeNumber  = c.salesRepEmployeeNumber
    GROUP BY o.officeCode
""", conn)

df_customers

# %% [markdown]
# ## Part 6: Subquery
#

# %% [markdown]
# ### Step 10
#
# Return employee number, first name, last name, office city and office code for employees who sold products ordered by fewer than 20 customers.
#

# %%
# CodeGrade step10
# Subquery first identifies product codes with < 20 distinct purchasers,
# then the outer query finds the employees who sold those products.
df_under_20 = pd.read_sql("""
    SELECT DISTINCT e.employeeNumber, e.firstName, e.lastName,
                    o.city, o.officeCode
    FROM employees e
    JOIN offices    o   ON e.officeCode      = o.officeCode
    JOIN customers  c   ON e.employeeNumber  = c.salesRepEmployeeNumber
    JOIN orders     ord ON c.customerNumber  = ord.customerNumber
    JOIN orderdetails od ON ord.orderNumber  = od.orderNumber
    WHERE od.productCode IN (
        -- Subquery: products purchased by fewer than 20 distinct customers
        SELECT p.productCode
        FROM products p
        JOIN orderdetails od2 ON p.productCode   = od2.productCode
        JOIN orders       o2  ON od2.orderNumber = o2.orderNumber
        GROUP BY p.productCode
        HAVING COUNT(DISTINCT o2.customerNumber) < 20
    )
""", conn)

df_under_20

# %% [markdown]
# ### Close the connection
#

# %%
# Run this cell without changes
conn.close()
