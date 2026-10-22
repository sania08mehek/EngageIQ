import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import OrgView from './pages/OrgView';
import TeamView from './pages/TeamView';
import EmployeeView from './pages/EmployeeView';
import PaceScore from './pages/PaceScore';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="dashboard" element={<OrgView />} />
        <Route path="dashboard/teams/:teamId" element={<TeamView />} />
        <Route path="dashboard/people/:employeeId" element={<EmployeeView />} />
        <Route path="pace-score" element={<PaceScore />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
