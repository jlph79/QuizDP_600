# DP-600 Quiz Application (v0.1)

This Streamlit-based application is designed to help users prepare for the DP-600 certification exam. It offers both study and exam practice modes, along with customizable settings.

## Project Structure

The application is divided into several Python files, each responsible for specific functionalities:

1. `main.py`: The entry point of the application.
2. `config.py`: Handles user-specific configurations.
3. `user.py`: Manages user authentication and registration.
4. `quiz.py`: Core quiz logic and progress tracking.
5. `question.py`: Represents individual quiz questions.
6. `case_study.py`: Represents case studies associated with questions.
7. `exam_session.py`: Manages individual exam attempts.
8. `database.py`: Sets up the SQLite database and defines schemas.
9. `utils.py`: Contains utility functions like loading questions and case studies.
10. `pages.py`: Defines different pages/modes of the application.

## File Dependencies

Here's a breakdown of the dependencies between the files:

- `main.py` depends on all other files.
- `quiz.py` depends on `question.py`, `case_study.py`, `exam_session.py`, and `database.py`.
- `user.py`, `config.py`, and `exam_session.py` depend on `database.py`.
- `question.py` and `case_study.py` are relatively independent but used by `quiz.py` and `pages.py`.
- `utils.py` depends on `question.py` and `case_study.py`.
- `pages.py` depends on `quiz.py` and `config.py`.

## File Hierarchy

```
DP-600_Quiz_App/
│
├── main.py
├── config.py
├── user.py
├── quiz.py
├── question.py
├── case_study.py
├── exam_session.py
├── database.py
├── utils.py
├── pages.py
├── requirements.txt
└── README.md
```

## Setup and Running the Application

1. Ensure you have Python 3.7+ installed.
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   streamlit run main.py
   ```

## Features

- User authentication and registration
- Study mode for reviewing questions
- Timed exam practice mode
- Customizable settings (font sizes, exam duration, number of questions)
- Progress saving and loading
- Support for multiple question types (multiple-choice, hotspot, drag-and-drop)
- Case study support

## Database

The application uses SQLite for data persistence. The database file `quiz_app.db` will be created in the same directory as the application files.

## Configuration

User-specific settings are stored in the database and can be modified through the Configuration page in the application.

## Known Issues and Limitations

- The application currently supports only local usage and doesn't have multi-user concurrent access support.
- Image paths are hardcoded and may need to be adjusted based on your local setup.
- There's no admin interface for adding or modifying questions; questions are loaded from a JSON file.

## Future Improvements

- Implement better error handling and logging
- Add an admin interface for managing questions and users
- Improve the UI/UX with more interactive elements
- Implement more sophisticated question types
- Add detailed analytics and performance tracking for users

## Contributing

Contributions to improve the application are welcome. Please fork the repository and submit a pull request with your changes.

## License

[MIT License](https://opensource.org/licenses/MIT)