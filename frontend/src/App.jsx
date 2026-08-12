import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Poll from './pages/Poll';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import CreateProject from './pages/CreateProject';
import ControlProjects from './pages/ControlProjects';
import FundingOptimizer from './pages/FundingOptimizer';
import CashFlowStatus from './pages/CashFlowStatus';
import PortfolioForm from './pages/PortfolioForm';
import PortfolioView from './pages/PortfolioView';
import Feedback from './pages/Feedback';
import Notifications from './pages/Notifications';
import InvestmentDetail from './pages/InvestmentDetail';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import VerifyEmail from './pages/VerifyEmail';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="login" element={<Login />} />
        <Route path="signup" element={<Signup />} />
        <Route path="forgot-password" element={<ForgotPassword />} />
        <Route path="reset-password" element={<ResetPassword />} />
        <Route path="verify-email" element={<VerifyEmail />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id" element={<ProjectDetail />} />
        <Route path="projects/:id/feedback" element={<ProtectedRoute><Feedback /></ProtectedRoute>} />

        <Route path="poll" element={<ProtectedRoute><Poll /></ProtectedRoute>} />
        <Route path="create-project" element={<ProtectedRoute role="founder"><CreateProject /></ProtectedRoute>} />
        <Route path="control-projects" element={<ProtectedRoute role="founder"><ControlProjects /></ProtectedRoute>} />
        <Route path="funding-optimizer" element={<ProtectedRoute role="founder"><FundingOptimizer /></ProtectedRoute>} />
        <Route path="cash-flow" element={<ProtectedRoute role="founder"><CashFlowStatus /></ProtectedRoute>} />
        <Route path="portfolio" element={<ProtectedRoute><PortfolioView /></ProtectedRoute>} />
        <Route path="portfolio/form" element={<ProtectedRoute><PortfolioForm /></ProtectedRoute>} />
        <Route path="portfolio/form/:id" element={<ProtectedRoute><PortfolioForm /></ProtectedRoute>} />
        <Route path="notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
        <Route path="investment/:id" element={<ProtectedRoute><InvestmentDetail /></ProtectedRoute>} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
