# Assignment3_AlgorithmicRedistricting_MSDS460

Each assignment in this course should be assigned to its own unique repository.

Developed by Thomas W. Miller. Revised September 18, 2024.

This is a workgroup assignment Every student should be working in a workgroup of three to five students.  If you are not a member of an active workgroup, contact the TA to ensure that you are placed in a workgroup. 

There is a discussion thread for this assignment.  Pay attention to this discussion thread because no two workgroups may select the same state. 

This assignment gives you a chance to learn about constrained optimization and integer programming from scratch. You will be gathering relevant data, setting objectives, defining constraints, and formulating a solution to a problem in U.S. government.

Redistricting is like an election in reverse. Usually, the voters get to pick the politicians. In redistricting, the politicians get to pick the voters.    —Thomas B. Hofeller  (Republican political strategist, See bio on WikipediaLinks to an external site.)                              

Just in case you think this problem has gone away or is no longer relevant for 2024, check out this January 18, 2024 article from ProPublica:

The Big Story: The Failed Promise of Independent Election MapmakingLinks to an external site.

And this article from CNN Politics:

          Redistricting fights in these states could determine which party controls the US HouseLinks to an external site.

Leigh McGowan's book A Return to Common Sense: How to Fix America Before We Really Blow It (McGowan 2024) includes discussion of Gerrymandering as one of many threats to democracy in the United States. McGowan has an online presence as POLITICSGIRLLinks to an external site.. Also, check out the September 17, 2024, interview on MSNBCLinks to an external site..

For this assignment, each workgroup will be working on its own problem (its own selected state), trying to define a fair and equitable redistricting plan, while assignment counties to legislative districts for a state selected from a special list of ten states. The list shows each state, along with its number of legislative districts (number of members in the U.S. House of Representatives for 2022) and its number of counties:

    Illinois (18, 102)    Pennsylvania (18, 67)    Ohio (16, 88)    Michigan (14, 83)    North Carolina (13, 100)

    New Jersey (12, 21)    Virginia (11, 95)    Washington (10, 39)    Indiana (9, 92)      Tennessee (9, 95)    

This assignment makes sense as a workgroup assignment for many reasons. (1) It begins with consensus building regarding the objective: How shall we define "fairness" in the assignment of counties to congressional districts?  The hope was that team members will work together in defining the objective. (2) The specification of constraints can be difficult, and the number of constraints can be large. Having a team of students working on this makes sense. (3) There may be a need to test many alternative solutions and to "tweak" solutions to the integer program that is developed. (4) Integer programs can take a long time to run and may require lots of memory. So, it is a good idea to get started on this assignment early, and it may be useful to have more than one person running the programs or trying alternative versions of programs.

Redistricting is a hard integer programming problem, in part, due to the numbers of decision variables and constraints. Consider a state like Georgia with 14 congressional districts and 159 counties, with, say 155 counties falling below a population level for direct assignment to congressional districts. We can define 14 x 155 = 2,170 binary decision variables where each variable is 1 if the county is assigned to a district and 0 if not. To go along with these decision variables, there will be thousands of constraints. Integer programming problems can be large. Fitting these problems into computer memory can be a challenge. Finding a solution within a reasonable amount of time can be a challenge.

There have been many attempts to arrive at a mathematical solution to the redistricting problem, as indicated by the lengthy list of references listed at the bottom of this assignment write-up. Check out the work of the MGGG Redistricting LabLinks to an external site., a research group at Tisch College of Tufts University, and its online resource for redistricting: DistrictrLinks to an external site..

This assignment calls for a particular approach to redistricting: an approach using integer programming. Redistricting can be thought of as a set partitioning problem with binary decision variables. To get started, note the problem setup defined in Becker and Solomon (2020).  That is, use population in the constraints only, while defining an objective that maximizes "compactness," or (alternatively) minimizes "lack of compactness." The challenge is to arrive at a mathematical rendering of "compactness."

How shall we deal with "compactness"?

As a thought experiment, suppose we define a new set of variables as products of binary variables representing pairs of counties, perhaps with costs as geographic distances between pairs of counties.  Georgia has 159 counties, with 155 falling below a population threshold for assigning representatives directly. All possible pairs of 155 counties yields (155*154)/2 = 11,925 variables to use in defining compactness constraints.

If we need to compute distances between pairs of county centroids (expressed in decimal latitude and longitude values), there are algorithms for doing so. Your instructor provides a zip archive showing Python code for distance calculations: GIS-distance-calculations-in-Python.zip Download GIS-distance-calculations-in-Python.zip. The zip archive provides example code and testing of GIS distance calculations in miles and meters obtained from longitude and latitude measures for two locations. It also shows UTM calculations in meters. The archive also provides an explanation of the Universal Transverse Mercator projection. The code was run under Python 3.9.16 on a Windows 10 system. Note that we may want to use latitude and longitude for distance measurements between counties or districts because some states will span more than one UTM zone. 

States relied on data from the 2020 US Census of Population informing their congressional districts. To see the data that were made available to states, use this link: https://api.census.gov/data/2020/dec/pl.htmlLinks to an external site.. The US Census Bureau provides information and training videosLinks to an external site. on how to gather relevant data using an application programming interface.

Assignment tasks. Each workgroup should

Obtain a complete list of counties for the selected state.
Obtain demographic data relating to the total population and the percentage of the population that is white only in each county.  These data should come from the US Census of Population from 2020 or later. A summary list is provided at https://worldpopulationreview.com/us-countiesLinks to an external site.  If possible, gather data relating to past statewide elections, so you can see proportions of votes for Democratic versus Republican candidates. 
Note counties that are geographically adjacent to one another: https://www2.census.gov/geo/docs/reference/county_adjacency.txtLinks to an external site.
Set partitioning. Use integer programming (set partitioning) to obtain an algorithmic/optimal redistricting. Assign every county in your selected state to exactly one congressional district while striving to meet your objective through maximization or minimization.
Population balance. Try to satisfy population balance (one-person-one-vote). That is, congressional districts should have approximately the same population. Consider strategies for assigning more than one representative to counties with high-population centers as long as elections are county-wide. Do not divide counties geographically.
Compact districts. Try to ensure that congressional districts geographically compact (are composed of counties that are adjacent to one another). Describe constraints or objectives employed to accomplish this goal. Note any difficulties encountered in setting up constraints or objectives.
Solve the integer programming problem using Python PuLP or AMPL.  Note any difficulties encountered, given the size of the integer programming problem.
Consider secondary goals of redistricting, such as encouraging equal representation across races. For example, you may try to achieve as much racial balance (percentage white alone versus other races) as possible across all congressional districts. Another secondary goal may be to ensure that the proportions of Democratic versus Republican representatives are approximately equal to the proportions of Democratic and Republican voters in recent statewide elections.
Prepare a written report of your work. One paper per workgroup. Members of the workgroup will share a common grade on this assignment with the understanding that all workgroup members contribute to the work.
The paper and deliverables (worth a total of 150 points) should address the following questions:

Data sources (30 points). What did you use for data sources? Do you have any concerns about these sources?
Specification (Objective function and Constraints) (30 points). How did you define the objective function? To what extent were you able to accommodate set covering, as well as the idea of defining geographically compact districts?  Did you use county adjacency information, district compactness measures, or distance metrics. How did you implement the principle of one-person-one-vote? 
Programming (30 points). Implement the linear programming problem using Python PuLP or AMPL. Provide the program code and output/listing as plain text files, posting within a GitHub repository dedicated to this assignment. 
Solution (30 points). What is the optimal redistricting solution for your state? Are you prepared to submit your redistricting plan to the state's legislature, the governor, or the courts? Or does the plan need more work? Do you have any concerns about your solution? 
Maps and discussion (30 points). Draw color-coded maps for your algorithmic/optimal redistricting and for the actual redistricting that was implemented by your selected state. How does your plan compare with other possible plans, such as a plan developed using the DistrictrLinks to an external site. utility? Which map would you recommend for your selected state?  Can either of these plans be described as "fair and equitable"?  To what extent are these plans consistent with the principle that citizens should have equal representation in voting (one person, one vote)? See Evenwel v. Abbott (2016). You may want to consult background information under References, as well as gerrrymandering on WikipediaLinks to an external site..
Deliverables (One submission per workgroup)

Remember to include all input data, programs/code, results/listings, and documentation in your GitHub repository.

One member of the workgroup should be designated as the workgroup leader, and this person should be placing the deliverables in the GitHub repository. Only one repository URL is needed for each workgroup.

Paper (pdf file). The paper/write-up should be submitted as a pdf file (double-spaced, 4 pages max). Think of the paper as comprising the methods and results sections of a written research report. Provide a paragraph or two on methods and a paragraph or two about results for each part of this assignment.  Include the redistricting maps within the paper. Submit the paper as a single pdf file with your workgroup number at the beginning of the file name such as workgroup-X-assignment-3.pdf

Program code (text link to GitHub repository). Key information from the paper should also be included in the README.md markdown file of a public GitHub repository established by the student who is submitting on behalf of the workgroup.  The GitHub repository should include text files for the program code (Python or AMPL), and program output (.txt extension). Excel files, if used, should also be included in the GitHub repository. Text files for programs (.R or .py extension for R or Python code) for making the maps should be included in the GitHub repository, along with image files (.jpg or .png extension). Include the web address text (URL) for the GitHub repository in the comments form of the assignment posting.  You should be providing a link to a separate repository that can be cloned. It should end with the .git extension.

Uploads are restricted to files with pdf, md, and txt extensions.

References 

Altman, Micah, and Michael P. McDonald. 2011. "BARD: Better Automated Redistricting." Journal of Statistical Software, 42(4). Available online at https://www.jstatsoft.org/article/view/v042i04Links to an external site..
Becker, Amariah, and Justin Solomon. 2020. “Redistricting Algorithms.” Online reference: https://arxiv.org/abs/2011.09504Links to an external site. Paper available at https://arxiv.org/pdf/2011.09504.pdfLinks to an external site.
Bullock, Charles, III. 2021. Redistricting: The Most Political Activity in America (second edition). Lanham, MD: Rowman & Littlefield. [ISBN-13: 978-1538149645]
Chen, Jowei, and Jonathan Rodden. 2015, December 17. "Cutting Through the Thicket: Redistricting Simulations and the Detection of Partisan Gerrymanders." Election Law Journal: Rules, Politics, and Policy, 14(4): 331–345. Available at https://www-liebertpub-com.turing.library.northwestern.edu/doi/pdfplus/10.1089/elj.2015.0317 
Duchin, Moon, and Olivia Walch (eds.) 2022. Political Geometry: Rethinking Redistricting in the US with Math, Law, and Everything in Between. Switzerland AG: Springer Nature. [ISBN-13: 978-3319691602] Available online at https://mggg.org/gerrybookLinks to an external site.
Evenwel v. Abbott. 2016, November 10. Harvard Law Review, 130(1): 387–396. Available online at https://harvardlawreview.org/2016/11/evenwel-v-abbott/Links to an external site.  and https://harvardlawreview.org/wp-content/uploads/2016/11/387-396_Online.pdfLinks to an external site.  
Hess, S. W., J. B. Weaver, H. J. Siegfeldt, J. N. Whelan, and P. A. Zitlau. 1965. "Nonpartisan Political Redistricting by Computer." Operations Research, 13(6): 998–1006.
Horvat, Sabi. 2021, April 2. How to Draw Congressional Districts in Python with Linear Programming. Retrieved from the World Wide Web, May 5, 2022, from Towards Data Science.Links to an external site.
Jacobs, Matt, and Olivia Walch. 2018. "A partial differential equations approach to defeating partisan gerrymandering." Available online at https://arxiv.org/pdf/1806.07725.pdfLinks to an external site..
McGann, Anthony, Charles Anthony Smith, Michael Latner, and Alex Keena. 2015, November 16. "A Discernable and Manageable Standard for Partisan Gerrymandering." Election Law Journal: Rules, Politics, and Policy, 14(4): 295–311. Available at https://www-liebertpub-com.turing.library.northwestern.edu/doi/epub/10.1089/elj.2015.0312 
McGowan, Leigh. 2024. A Return to Common Sense: How to Fix America Before We Really Blow It. New York: Atria. [ISBN-13: 978-1-6680-6643-0] See Principle 3: Every Citizen Should Have a Vote and That Vote Should Count, pages 121–154. (Chapter requested for Course Reserves)
Mehrotra, Anuj, Ellis L. Johnson, and George L. Nemhauser. 1998, August 1. "An Optimization Based Heuristic for Political Districting." Management Science, 44(8): 1021–1166.
Miller, Thomas W. 2015. Modeling Techniques in Predictive Analytics with Python and R: A Guide to Data Science. Upper Saddle River, NJ: Pearson Education. [ISBN-13: 978-0-13-389206-2] Repository of Python and R code on GitHubLinks to an external site..
Niemi, Richard G, Bernard Grofman, Carl Carlucci, and Thomas Hofeller. 1990, November. "Measuring Compactness and the Role of a Compactness Standard in a Test for Partisan and Racial Gerrymandering." The Journal of Politics, 52(4): 1155–1181. 
Ricca, Federica and Andrea Scozzari. 2020, February. "Mathematical Programming Foundations for Practical Political Districting," In Ríos-Mercado, R. (eds), Optimal Districting and Territory Design, International Series in Operations Research & Management Science, 284: 105–128, New York: Springer. [ISBN-13: 978-3-030-34311-8] Has extensive bibliography of redistricting references, which can be viewed on from Springer onlineLinks to an external site.. Available on Course Reserves.
Reichert, Jeff, writer, director, and producer. 2010. Gerrymandering. Green Film Company, DVD motion picture. Available from Course Reserves.
Seabrook, Nicholas R. 2017. Drawing the Lines: Constraints on Partisan Gerrymandering in U.S. Politics. Ithaca, NY: Cornell University Press. [ISBN-13: 978-1501705311] This is an exceptional scholarly resource that shows that states must follow legal constraints in redistricting. The principle of one person, one vote applies to all states. Individual states have additional legal constraints associated with compactness, continuity, and the degree to which new districts must conform to old districts. Here is a summary: Legal-Constraints-on-Redistricting-by-State.pdfDownload Legal-Constraints-on-Redistricting-by-State.pdf
Seabrook, Nicholas R. 2022. One Person, One Vote: A Surprising History of Gerrymandering in America. Ney York: Pantheon Books. [ISBN-13: 978-059331586-6]
Shmoys, David B. 2022, February 25. Algorithmic Tools for U.S. Congressional Districting: Fairness via Analytics. Presentation hosted by C3 Digital Transformation Institute. Available online at https://www.youtube.com/watch?v=furGsyRhNuYLinks to an external site.
Validi,Hamidreza, Austin Buchanan, and Eugene Lykhovyd. 2022, March–April. "Imposing Contiguity Constraints in Political Districting Models." Operations Research, 70(2): 867-892. GitHub C++ code repository at https://github.com/zhelih/districtingLinks to an external site. . Online abstract and link to paper at http://www.optimization-online.org/DB_HTML/2020/01/7582.htmlLinks to an external site. Presentation slides at: https://github.com/zhelih/districting/blob/master/Districting_slides.pdfLinks to an external site. 
Williams, H. Paul. 2013. Model Building in Mathematical Programming (fifth ed.). New York: Wiley. [ISBN-13: 978-111844333-0] See section 9.5.3 on set partitioning, pages 193–194. Companion website at https://bcs.wiley.com/he-bcs/Books?action=index&bcsId=8095&itemId=1118443330Links to an external site.
World Population Review. 2022. Online source for the number of representatives by state. Available at https://worldpopulationreview.com/state-rankings/number-of-representatives-by-stateLinks to an external site. 
 
