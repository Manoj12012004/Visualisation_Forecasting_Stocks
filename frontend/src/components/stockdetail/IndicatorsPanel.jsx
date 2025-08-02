import React, { useEffect, useRef, useState } from "react";
import api from "../../services/api";
import {
  Card, Stack, FormGroup, FormControlLabel, Checkbox,
  Select, MenuItem, InputLabel, FormControl, CircularProgress, Typography, Divider
} from "@mui/material";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine
} from "recharts";
import { DatePicker, LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { TextField } from "@mui/material";
import dayjs from "dayjs";

const INDICATORS = [
  { key: "RSI", label: "RSI", yAxisId: "right", color: "#e53935" },
  { key: "MACD", label: "MACD", yAxisId: "right", color: "#1e88e5" },
  { key: "Signal", label: "Signal", yAxisId: "right", color: "#ffb300" },
  { key: "SMA_20", label: "SMA 20", yAxisId: "left", color: "#43a047" },
  { key: "SMA_50", label: "SMA 50", yAxisId: "left", color: "#8e24aa" },
];

const INTERVALS = ["1min", "5min", "15min", "1h", "1day"];

function IndicatorsPanel({ symbol }) {
  const [data, setData] = useState([]);
  const [visible, setVisible] = useState(
    INDICATORS.reduce((acc, ind) => ({ ...acc, [ind.key]: true }), {})
  );
  const [range, setRange] = useState({ start: 0, end: 12 });
  const [interval, setInterval] = useState("1day");
  const [startDate, setStartDate] = useState(dayjs().subtract(1, "month"));
  const [endDate, setEndDate] = useState(dayjs());
  const [loading, setLoading] = useState(false);

  const chartref = useRef(null);

  // Sync data fetch with parameters
  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    const params = new URLSearchParams({
      interval,
      start_date: startDate.format("YYYY-MM-DD"),
      end_date: endDate.format("YYYY-MM-DD"),
    });
    api
      .get(`/stocks/${symbol}/technical?${params.toString()}`)
      .then((res) => {
        const sortedData = [...res.data].sort(
          (a, b) => new Date(a.datetime) - new Date(b.datetime)
        );
        const formattedData = sortedData.map((entry) => ({
          ...entry,
          date: new Date(entry.datetime).toLocaleString("en-US", {
            year: "numeric", month: "2-digit", day: "2-digit"
          }),
        }));
        setData(formattedData);
        setRange({
          start: Math.max(0, formattedData.length - 12),
          end: formattedData.length
        });
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [symbol, interval, startDate, endDate]);

  // Touchpad/mouse zoom
  useEffect(() => {
    const chartdiv = chartref.current;
    if (!chartdiv) return;
    const onWheel = (e) => {
      e.preventDefault();
      if (e.deltaY < 0) {
        handleZoom("in");
      } else {
        handleZoom("out");
      }
    };
    chartdiv.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      chartdiv.removeEventListener("wheel", onWheel);
    };
    // Include range and data as deps so new window logic applies on update
  }, [range, data]);

  const handleZoom = (type) => {
    const size = range.end - range.start;
    const length = data.length;
    if (type === "in" && size > 5)
      setRange({ start: range.start + 1, end: range.end - 1 });
    else if (type === "out") {
      setRange({
        start: Math.max(0, range.start - 1),
        end: Math.min(length, range.end + 1),
      });
    }
  };

  const toggleIndicator = (key) =>
    setVisible((prev) => ({ ...prev, [key]: !prev[key] }));

  const currentData = data.slice(range.start, range.end);

  return (
    <Card elevation={2} sx={{ p: 3, mb: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" gap={2} flexWrap="wrap">
        <Typography variant="h6">Technical Indicators</Typography>
        <Stack direction="row" gap={2} alignItems="center" flexWrap="wrap">
          <FormControl size="small">
            <InputLabel>Interval</InputLabel>
            <Select
              label="Interval"
              value={interval}
              onChange={e => setInterval(e.target.value)}
              sx={{ minWidth: 90 }}
            >
              {INTERVALS.map((iv) => (
                <MenuItem key={iv} value={iv}>{iv}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DatePicker
              label="Start Date"
              value={startDate}
              onChange={setStartDate}
              maxDate={endDate}
              slots={{ textField: TextField }}
              enableAccessibleFieldDOMStructure={false}
            />
            <DatePicker
              label="End Date"
              value={endDate}
              onChange={setEndDate}
              minDate={startDate}
              slots={{ textField: TextField }}
              enableAccessibleFieldDOMStructure={false}
            />
          </LocalizationProvider>
        </Stack>
      </Stack>
      <Divider sx={{ my: 2 }} />
      <FormGroup row sx={{ mb: 2 }}>
        {INDICATORS.map((ind) => (
          <FormControlLabel
            key={ind.key}
            control={
              <Checkbox
                checked={visible[ind.key]}
                onChange={() => toggleIndicator(ind.key)}
                sx={{ color: ind.color }}
              />
            }
            label={ind.label}
          />
        ))}
      </FormGroup>

      {/* No explicit zoom buttons - zoom is now scroll/touchpad! */}

      <div ref={chartref} style={{ width: "100%", height: 340, position: "relative" }}>
        {loading ? (
          <div style={{ height: 300, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <CircularProgress />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={currentData}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis
                yAxisId="left"
                label={{ value: "Price (SMA)", angle: -90, position: "insideLeft" }}
                domain={["auto", "auto"]}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                domain={[-100, 100]}
                label={{ value: "RSI / MACD", angle: 90, position: "insideRight" }}
              />
              <Tooltip
                labelFormatter={value => `Date: ${value}`}
                formatter={(val, name) => [<b>{val}</b>, name]}
              />
              <Legend verticalAlign="top" height={36}/>
              <ReferenceLine y={70} yAxisId="right" stroke="#e53935" strokeDasharray="3 3" label="RSI 70"/>
              <ReferenceLine y={30} yAxisId="right" stroke="#e53935" strokeDasharray="3 3" label="RSI 30"/>
              <ReferenceLine y={0} yAxisId="right" stroke="#bdbdbd" strokeDasharray="3 3" label="MACD 0"/>
              {INDICATORS
                .filter(ind => visible[ind.key])
                .map((ind) => (
                  <Line
                    key={ind.key}
                    type="monotone"
                    dataKey={ind.key}
                    stroke={ind.color}
                    yAxisId={ind.yAxisId}
                    dot={false}
                    strokeWidth={2}
                    isAnimationActive
                  />
                ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}

export default IndicatorsPanel;
