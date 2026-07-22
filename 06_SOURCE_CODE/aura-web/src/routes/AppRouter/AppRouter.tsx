import {
    BrowserRouter,
    Navigate,
    Route,
    Routes,
} from "react-router-dom";

import Landing from "../../pages/Landing";
import Authentication from "../../pages/Authentication";
import Login from "../../pages/Login";
import Register from "../../pages/Register";

import Dashboard from "../../pages/Dashboard";
import Agents from "../../pages/Agents";
import Research from "../../pages/Research";
import Chat from "../../pages/Chat";
import Memory from "../../pages/Memory";
import Knowledge from "../../pages/Knowledge";
import Files from "../../pages/Files";
import Automations from "../../pages/Automations";
import Models from "../../pages/Models";
import Analytics from "../../pages/Analytics";
import Brain from "../../pages/Brain";
import Laboratory from "../../pages/Laboratory";
import CloudOS from "../../pages/CloudOS";
import Evolution from "../../pages/Evolution";
import AIAssistant from "../../pages/AIAssistant";
import Security from "../../pages/Security";
import Studio from "../../pages/Studio";
import Settings from "../../pages/Settings";
import Profile from "../../pages/Profile";
import Admin from "../../pages/Admin";

import NotFound from "../../pages/NotFound";

import ProtectedRoute from "../ProtectedRoutes";

const AppRouter = () => {

    return (

        <BrowserRouter>

            <Routes>

                {/* Public */}

                <Route
                    path="/"
                    element={<Landing />}
                />

                <Route
                    path="/authentication"
                    element={<Authentication />}
                />

                <Route
                    path="/login"
                    element={<Login />}
                />

                <Route
                    path="/register"
                    element={<Register />}
                />

                {/* Protected */}

                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/agents"
                    element={
                        <ProtectedRoute>
                            <Agents />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/research"
                    element={
                        <ProtectedRoute>
                            <Research />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/chat"
                    element={
                        <ProtectedRoute>
                            <Chat />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/memory"
                    element={
                        <ProtectedRoute>
                            <Memory />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/knowledge"
                    element={
                        <ProtectedRoute>
                            <Knowledge />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/files"
                    element={
                        <ProtectedRoute>
                            <Files />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/automations"
                    element={
                        <ProtectedRoute>
                            <Automations />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/models"
                    element={
                        <ProtectedRoute>
                            <Models />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/analytics"
                    element={
                        <ProtectedRoute>
                            <Analytics />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/brain"
                    element={
                        <ProtectedRoute>
                            <Brain />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/laboratory"
                    element={
                        <ProtectedRoute>
                            <Laboratory />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/cloud"
                    element={
                        <ProtectedRoute>
                            <CloudOS />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/evolution"
                    element={
                        <ProtectedRoute>
                            <Evolution />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/assistant"
                    element={
                        <ProtectedRoute>
                            <AIAssistant />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/security"
                    element={
                        <ProtectedRoute>
                            <Security />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/studio"
                    element={
                        <ProtectedRoute>
                            <Studio />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/settings"
                    element={
                        <ProtectedRoute>
                            <Settings />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/profile"
                    element={
                        <ProtectedRoute>
                            <Profile />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/admin"
                    element={
                        <ProtectedRoute>
                            <Admin />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/home"
                    element={
                        <Navigate
                            to="/dashboard"
                            replace
                        />
                    }
                />

                <Route
                    path="*"
                    element={<NotFound />}
                />

            </Routes>

        </BrowserRouter>

    );

};

export default AppRouter;