import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const PriceChart = ({ width = "100%", height = 400 }) => {
  const [historicalData, setHistoricalData] = useState([]);
  const [endDate, setEndDate] = useState("");
  const [predictedData, setPredictedData] = useState([]);
  const [plotData, setPlotData] = useState([]);

  // Function to fetch historical data
  const fetchData = () => {
    axios
      .get("https://flask-app-57kgqhzrxq-no.a.run.app/get-graph")
      .then((response) => {
        const { hist } = response.data;
        const formattedData = Object.keys(hist).map((date) => ({
          date,
          histPrice: hist[date],
          predPrice: null,
          lower: null,
          upper: null,
        }));
        setHistoricalData(formattedData);
        setPlotData(formattedData); // Initialize plotData with historical data
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
      });
  };

  // Function to handle prediction
  const handlePredict = () => {
    const formData = new FormData();
    formData.append("end_date", endDate);

    axios
      .post("https://flask-app-57kgqhzrxq-no.a.run.app/predict", formData)
      .then((response) => {
        const predData = response.data[1].pred;

        const formattedPredictions = Object.keys(predData).map((date) => ({
          date,
          histPrice: null,
          predPrice: predData[date].pred,
          lower: predData[date].pred_lower,
          upper: predData[date].pred_upper,
        }));

        setPredictedData(formattedPredictions);
        setPlotData([...historicalData, ...formattedPredictions]);
      })
      .catch((error) => {
        console.error("Error predicting data:", error);
      });
  };

  // Function to handle refresh
  const handleRefresh = () => {
    setEndDate("");
    setPredictedData([]);
    fetchData();
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div>
      <button onClick={handleRefresh}>Refresh to Reset</button>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handlePredict();
        }}
      >
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          required
        />
        <button type="submit">Predict</button>
      </form>
      <ResponsiveContainer width={width} height={height}>
        <LineChart
          data={plotData} // Use combined plot data for the chart
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="histPrice"
            stroke="#8884d8"
            name="Historical Price"
          />
          <Line
            type="monotone"
            dataKey="predPrice"
            stroke="#FFD700"
            name="Predicted Price"
          />
          <Line
            type="monotone"
            dataKey="lower"
            stroke="#FF0000"
            name="Lower Bound"
            strokeDasharray="5 5"
          />
          <Line
            type="monotone"
            dataKey="upper"
            stroke="#00FF00"
            name="Upper Bound"
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PriceChart;
