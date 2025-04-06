import React, { useState } from "react";
import axios from "axios";

function App() {
  const [task, setTask] = useState("");
  const [output, setOutput] = useState([]);

  const runTask = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/run-task/", {
        task_name: task,
      });
      if (response.data.status === "success") {
        setOutput(response.data.output);
      } else {
        alert("Error: " + response.data.message);
      }
    } catch (error) {
      alert("Error running task: " + error.message);
    }
  };

  return (
    <div>
      <h1>DBAgent Front-End</h1>

      <div>
        <h2>Run Task</h2>
        <input
          type="text"
          placeholder="Enter task"
          value={task}
          onChange={(e) => setTask(e.target.value)}
        />
        <button onClick={runTask}>Run Task</button>
      </div>

      <div>
        <h2>Task Output</h2>
        <ul>
          {output.map((entry, index) => (
            <li key={index}>{JSON.stringify(entry)}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;