import React from "react";
import "./App.css";
import PriceChart from "./components/DataVisualz";

function App() {
  return (
    <div className="App">
      <h1>Electricity Price Visualization</h1>
      <PriceChart />
    </div>
  );
}

export default App;
