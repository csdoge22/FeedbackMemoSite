import { useEffect, useState } from 'react';
import Navbar from '../site_components/navbar';
const Signup = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    return (
        <>
            <Navbar />
            <div className="">

            </div>
        </>
    )
}
export default Signup;