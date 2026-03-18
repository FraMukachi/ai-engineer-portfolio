# Variables — storing data
name = "Fra"
age = 25
is_learning = True

# Strings — working with text
greeting = f"Hello, my name is {name}"
print(greeting)

# Functions — reusable blocks of code
def introduce(name, skill):
        return f"I am {name} and I am learning {skill}"

        result = introduce("Fra", "AI Engineering")
        print(result)

        # Lists — storing multiple items
        skills = ["Python", "FastAPI", "AI APIs"]
        print(f"My skills: {skills}")

        # Loops — doing things repeatedly
        for skill in skills:
                print(f"Learning: {skill}")


        # Dictionaries — storing data with labels
        person = {"name":"Fra","country": "South Africa","skills":["Python","FastAPI","AI APIs"],"learning": "AI Engineering"}            
        print(person["name"])
        print(person["country"])           
        print(person["skills"])

        # You can also loop through a dictionary
        for key, value in person.items():
          print(f"{key}: {value}")