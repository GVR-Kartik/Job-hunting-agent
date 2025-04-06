from typing import Dict, List
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.google import Gemini
import time

from firecrawl import FirecrawlApp
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class NestedModel1(BaseModel):
    """Schema for job posting data"""
    region: str = Field(description="Region or area where the job is located", default=None)
    role: str = Field(description="Specific role or function within the job category", default=None)
    job_title: str = Field(description="Title of the job position", default=None)
    experience: str = Field(description="Experience required for the position", default=None)
    job_link: str = Field(description="Link to the job posting", default=None)
class ExtractSchema(BaseModel):
    """Schema for job postings extraction"""
    job_postings: List[NestedModel1] = Field(description="List of job postings")

class FirecrawlResponse(BaseModel):
    """Schema for Firecrawl API response"""
    success: bool
    data: Dict
    status: str
    expiresAt: str

class JobHuntingAgent:
    """Agent responsible for finding jobs and providing recommendations"""
    
    def __init__(self, firecrawl_api_key=""): #use your own
        self.agent = Agent(
            model = Gemini(id="gemini-2.0-flash", api_key=""),#use your own
            markdown=True,
            description="I want you to act as an ATS expert. First, analyze the following job description and my resume text." \
            " Then, provide an ATS compatibility score and feedback on how well my resume aligns with the job description." \
            " Also, offer suggestions on how to improve my resume to increase my chances of passing through an ATS."
        )
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

    def find_jobs(
        self, 
        job_title: str,
        location: str,
        experience_years: int,
        skills: List[str]
    ) -> str:
        """Find and analyze jobs based on user preferences"""
        formatted_job_title = job_title.lower().replace(" ", "-")
        formatted_location = location.lower().replace(" ", "-")
        skills_string = ", ".join(skills)
        
        urls = [
            f"https://www.naukri.com/{formatted_job_title}-jobs-in-{formatted_location}?experience={experience_years}",
            f"https://www.naukri.com/{formatted_job_title}-jobs-in-{formatted_location}-2?experience={experience_years}",
            f"https://www.naukri.com/{formatted_job_title}-jobs-in-{formatted_location}-3?experience={experience_years}",
            f"https://www.indeed.com/jobs?q={formatted_job_title}&l={formatted_location}"
            # f"https://www.monster.com/jobs/search/?q={formatted_job_title}&where={formatted_location}",
        ]
        
        print(f"Searching for jobs with URLs: {urls}")
        
        try:
            raw_response = self.firecrawl.extract(
                urls=urls,
                params={
                    'prompt': f"""Extract job postings by region, roles, job titles, and experience from these job sites.
                    
                    Look for jobs that match these criteria:
                    - Job Title: Should be related to {job_title}
                    - Location: {location} (include remote jobs if available)
                    - Experience: Around {experience_years} years
                    - Skills: Should match at least some of these skills: {skills_string}
                    - Job Type: Full-time, Part-time, Contract, Temporary, Internship
                    
                    Goal : to extract only the urls having 12 digits number at ending (e.g., "https://www.naukri.com/job-listings-java-developer-ab-pan-india-infosys-pune-chennai-bengaluru-3-to-8-years-040425019070")
                    IMPORTANT: Return data for at least 20 different job opportunities.
                    """,
                    'schema': ExtractSchema.model_json_schema()
                }
            )
            
            # print("Raw Job Response:", raw_response)
            
            if isinstance(raw_response, dict) and raw_response.get('success'):
                jobs = raw_response['data'].get('job_postings', [])
            else:
                jobs = []
                
            # print("Processed Jobs:", jobs)
            c=0
            for each in jobs:
                self.find_job_description(c,each["job_link"])
                time.sleep(10)
                c+=1
            
            if not jobs:
                return "No job listings found matching your criteria. Try adjusting your search parameters or try different job sites."
            
            analysis = self.agent.run(
                f"""As a json response expert, analyze json job opportunities:

                Jobs Found in json format:
                {jobs}

                and give me the links in order by serialize to extract only the urls having 12 digits number at ending (e.g., "https://www.naukri.com/job-listings-java-developer-ab-pan-india-infosys-pune-chennai-bengaluru-3-to-8-years-040425019070")
                """
            )
            
            return analysis.content
        except Exception as e:
            print(f"Error in find_jobs: {str(e)}")
            return f"An error occurred while searching for jobs: {str(e)}\n\nPlease try again with different search parameters or check if the job sites are supported by Firecrawl."


    def find_job_description(self,c, link: str) -> str:
            
            print(f"Getting job desription for job with URL : {link}")
            
            try:
                raw_response = self.firecrawl.extract(
                    urls=[link],
                    params={
                        'prompt': f"""Extract all technical and functional skills required for the job from the job description provided, 
                        including programming languages, frameworks, tools, methodologies, and any other relevant skills of this """
                    }
                )
                
                print("Job Description :- ", raw_response)
                
            except Exception as e:
                print(f"Error in getting job_description: {str(e)}")
                return f"An error occurred while searching for jobs: {str(e)}\n\nPlease try again with different search parameters or check if the job sites are supported by Firecrawl."
            
            education="""\section{Education }
                            \resumeSubHeadingListStart

                            \resumeSubheading
                            {NIT Rourkela}{May 2022}
                            {Bachelor of Technology in Electronics and Communication (Electrical Minor)}{Rourkela, India}
                            \resumeItemListStart
                                \resumeItem{\textbf{CGPA:} 8.7 / 10}
                                \resumeItem{\textbf{Relevant Coursework:} Data Structures and Algorithms, Object-Oriented Programming (Java), Database Management Systems , Operating Systems, Design Patterns,  Cloud Computing}
                            \resumeItemListEnd

                            \resumeSubHeadingListEnd
                        """
            technical_skills="""\section{Technical Skills}
                                \begin{itemize}[leftmargin=0.15in, label={}]
                                \small{\item{
                                    \textbf{Languages}{: Java, Python, C++, PL / SQL, MongoDB} \\
                                    \textbf{Frameworks}{: Spring Boot, Spring MVC, Hibernate, JPA, Spring Cloud, Kafka} \\
                                    \textbf{Technologies}{: REST (JAX-RS), SOAP (JAX-WS), GraphQL, Docker, Kubernetes, AWS, Jenkins, CI/CD, Redis, Elasticsearch} \\
                                    \textbf{Tools}{: Maven, Gradle, IntelliJ IDEA, Eclipse, Git, Jira, Jenkins, Chef, Power BI, Nginx, Zookeeper} \\
                                    \textbf{Databases}{: MySQL, SQL Server, Oracle, MongoDB} \\
                                    \textbf{Certifications}{: AWS Certified Cloud Practitioner, Elastic Certified Analyst} \\
                                }}
                                \end{itemize}"""
            Experience="""\section{Experience }
                    \resumeSubHeadingListStart

                        \resumeSubheading
                        {Barclays}{Aug 2022 -- Present}
                        {Graduate Analyst}{Pune, India}
                        \resumeItemListStart
                            \resumeItem{Developed RESTful services and APIs for ATM cash management, achieving 95\%, code coverage.}
                            \resumeItem{Built a predictive Spring Boot solution to forecast daily cash needs and automated data provisioning using MySQL stored procedures.}
                            \resumeItem{Defined and documented RESTful APIs using GraphQL, Swagger \& RAML, improving cross-team collaboration and API contract clarity, reducing server-side operations by 4 hours weekly.}
                            \resumeItem{Led Spring (v3 to v5) and Gradle (v5.6 to v8) upgrades across 31 mini apps, improving performance by 25\%.}
                            \resumeItem{Integrated Kafka with Prometheus using Python to enhance data flow observability, boosting operational efficiency by 20\%.}
                            \resumeItem{Designed, implemented, and automated CI/CD pipelines with Jenkins, GitFlow, and Bitbucket for ELK stack deployments, improving deployment efficiency by 30\%.}
                            \resumeItem{Built a Spring Boot service for real-time Kibana dashboards, cutting reporting time by 40\%.}
                            \resumeItem{Automated the merge of pull requests by integrating Bitbucket with ServiceNow API for repositories, reducing manual effort by 5 hours on weekends and improving work-life balance.}
                            \resumeItem{Upgraded Struts framework in legacy applications as part of tech modernization, ensuring compliance and reducing security vulnerabilities by 40\%.}

                        \resumeItemListEnd

                        \resumeSubheading
                        {Barclays}{May 2021 -- Jun 2021}
                        {Graduate Analyst Intern}{Remote}
                        \resumeItemListStart
                            \resumeItem{Engineered scalable microservices architecture using Java 8, Spring Boot, and RESTful APIs, delivering reliable enterprise applications.}
                            \resumeItem{Implemented Test-Driven Development (TDD) practices with 98\%, code coverage, significantly reducing defects and improving maintainability.}
                            \resumeItem{Optimized batch processing workflows with Spring Batch, reducing processing time by 30\%.}
                            \resumeItem{Developed and optimized SQL (H-2) and NoSQL (MongoDB) database interactions, improving query performance by 25\%.}
                        \resumeItemListEnd

                    \resumeSubHeadingListEnd
                    """
            analysis = self.agent.run(
                f"""I want you to act as an ATS expert. 
                First, analyze the following job description :- {raw_response} and 
                here is my education :{education}, techical skills :{technical_skills} and my experience :{Experience}. 
                Then, provide an ATS compatibility score out of 100 and feedback on how well my resume currently aligns with the job description. 
                Also, offer suggestions on how to improve my resume to increase my chances of passing through an ATS, give me updated ones in latex format
                also don't ask me to update the latex format just give me suggestions in the latex format i have already given , i like my latex formatting
                i just need suggestions in text inside it.
                (e.g. like update this part in experience and update this part in technical skills to get above 90% match)
                """
            )
           
            with open("output.txt", "a") as file:
                file.write(f"{c}. Job link :- [ {link} ] and my analysis :- {analysis.content}\n\n\n")
                file.write("----------x--------NEXT JOB----------x--------\n\n\n")

            time.sleep(10)
            print("Waited for 20 sec")


def main():
    

    env_firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "") # use ur own
    
    try:
        job_agent=JobHuntingAgent(env_firecrawl_key)

        # job_results = job_agent.find_jobs(
        #     job_title=input("job_title : "),
        #     location=input("location : "),
        #     experience_years=input("experience_years : "),
        #     skills=input("skills : ")
        # )
        job_results = job_agent.find_jobs(
            job_title="java",
            location="bangalore",
            experience_years="3",
            skills="java"
        )

        # print(job_results)
        
            
        
    except Exception as e:
        error_message = str(e)
        print(f"❌ An error occurred: {error_message}")

if __name__ == "__main__":
    main() 