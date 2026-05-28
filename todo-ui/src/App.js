import { useEffect, useState } from "react";
import axios from "axios";
import Calendar from "react-calendar";
import "react-calendar/dist/Calendar.css";
import "./App.css";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [date, setDate] = useState(new Date());
  const [taskName, setTaskName] = useState("");
  const [priority, setPriority] = useState("Medium");

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    const res = await axios.get(`${API}/tasks`);
    setTasks(res.data);
  };

  const addTask = async () => {
    if (!taskName) return;

    await axios.post(`${API}/tasks`, {
      name: taskName,
      date: date.toISOString().split("T")[0],
      priority
    });

    setTaskName("");
    fetchTasks();
  };

  const toggleComplete = async (task) => {
    await axios.put(`${API}/tasks/${task.id}`, {
      status: task.status === "Completed" ? "Pending" : "Completed"
    });

    fetchTasks();
  };

  const deleteTask = async (id) => {
    await axios.delete(`${API}/tasks/${id}`);
    fetchTasks();
  };

  const selectedDate = date.toISOString().split("T")[0];

  const filteredTasks = tasks.filter(
    (t) => new Date(t.date).toISOString().split("T")[0] === selectedDate
  );

  const progress =
    filteredTasks.length === 0
      ? 0
      : Math.round(
          (filteredTasks.filter((t) => t.status === "Completed").length /
            filteredTasks.length) *
            100
        );

  const priorityColor = (p) => {
    if (p === "High") return "#ff6b6b";
    if (p === "Medium") return "#feca57";
    return "#1dd1a1";
  };

  return (
    <div className="app">

      <h1>📅 Task Planner</h1>

      <div className="calendar-box">
        <Calendar onChange={setDate} value={date} />
      </div>

      {/* SMALL CENTER BOX */}
      <div className="task-box">

        <h3>Tasks for {selectedDate}</h3>

        <div className="progress-bar">
          <div className="fill" style={{ width: `${progress}%` }} />
        </div>

        <p>{progress}% completed</p>

        <div className="add-box">
          <input
            placeholder="Enter task..."
            value={taskName}
            onChange={(e) => setTaskName(e.target.value)}
          />

          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>

          <button onClick={addTask}>➕ Add</button>
        </div>

        <div className="task-list">

          {filteredTasks.map((task) => (
            <div className="task" key={task.id}>

              {/* TASK TEXT NOW BLACK */}
              <span
                className="task-text"
                style={{ color: "#000" }}
              >
                {task.name}
              </span>

              <div className="btns">

                <button
                  className={task.status === "Completed" ? "done" : "btn"}
                  onClick={() => toggleComplete(task)}
                >
                  {task.status === "Completed" ? "Done ✔" : "Complete"}
                </button>

                <button
                  className="delete"
                  onClick={() => deleteTask(task.id)}
                >
                  Delete 🗑
                </button>

              </div>

            </div>
          ))}

          {filteredTasks.length === 0 && (
            <p className="empty">No tasks for this date</p>
          )}

        </div>
      </div>
    </div>
  );
}