import { Link, useLocation } from "react-router-dom";
import { useAuth } from "./authcontext";
import { useState } from "react";

const Navbar = () => {
    const location = useLocation();
    const { isAuthenticated, logout } = useAuth();
    const [accountDropdown, setAccountDropdown] = useState(false);

    const linkClasses = (path: string) =>
        "block py-2 px-3 rounded-sm md:bg-transparent md:p-0 " +
        (location.pathname === path
            ? "text-white bg-blue-700 md:text-blue-700 dark:text-white md:dark:text-blue-500"
            : "text-gray-900 hover:bg-gray-100 md:hover:bg-transparent md:hover:text-blue-700 dark:text-white md:dark:hover:text-blue-500 dark:hover:bg-gray-700 dark:hover:text-white md:dark:hover:bg-transparent"
        );

    return (
        <nav className="bg-white border-gray-200 dark:bg-gray-900">
            <div className="max-w-screen-xl mx-auto p-4">
                <div className="w-full flex justify-center">
                    <ul className="font-medium flex flex-row space-x-8 bg-gray-50 border border-gray-100 rounded-lg p-4 md:bg-white md:border-0 dark:bg-gray-800 md:dark:bg-gray-900 dark:border-gray-700">
                        <li>
                            <Link to="/" className={linkClasses("/")}>Home</Link>
                        </li>
                        <li>
                            <Link to="/about" className={linkClasses("/about")}>About</Link>
                        </li>
                        {!isAuthenticated ? (
                            <>
                                <li>
                                    <Link to="/signup" className={linkClasses("/signup")}>Sign Up</Link>
                                </li>
                                <li>
                                    <Link to="/login" className={linkClasses("/login")}>Login</Link>
                                </li>
                            </>
                        ) : (
                            <>
                                <li>
                                    <Link to="/dashboard" className={linkClasses("/dashboard")}>Dashboard</Link>
                                </li>
                                <li className="relative">
                                    <button
                                        className="block py-2 px-3 rounded-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
                                        onClick={() => setAccountDropdown((open) => !open)}
                                    >
                                        Account ▼
                                    </button>
                                    {accountDropdown && (
                                        <ul className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded shadow-lg z-10">
                                            <li>
                                                <Link to="/change-email" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">Change Email</Link>
                                            </li>
                                            <li>
                                                <Link to="/change-username" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">Change Username</Link>
                                            </li>
                                            <li>
                                                <Link to="/change-password" className="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">Change Password</Link>
                                            </li>
                                            <li>
                                                <button
                                                    onClick={logout}
                                                    className="block w-full text-left px-4 py-2 text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700"
                                                >
                                                    Logout
                                                </button>
                                            </li>
                                        </ul>
                                    )}
                                </li>
                            </>
                        )}
                    </ul>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;