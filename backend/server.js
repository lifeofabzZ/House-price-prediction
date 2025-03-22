const express = require("express");
const dotenv = require("dotenv");
const connectDB = require("./src/config/db");
const authRoutes = require("./src/routes/authRoutes");
const cors = require("cors");

dotenv.config();
connectDB();

const app = express();  // ✅ Define `app` before using it

app.use(cors());  // ✅ Now use `cors`
app.use(express.json());
app.use("/api/auth", authRoutes);

app.listen(5000, () => console.log("Server running on port 5000"));
